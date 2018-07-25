QObject = (name, data, webChannel) ->
  `var name`

  addSignal = (signalData, isPropertyNotifySignal) ->
    signalName = signalData[0]
    signalIndex = signalData[1]
    object[signalName] =
      connect: (callback) ->
        if typeof callback != 'function'
          console.error 'Bad callback given to connect to signal ' + signalName + ' Type:' + typeof callback.toString()
          return
        object.__objectSignals__[signalIndex] = object.__objectSignals__[signalIndex] or []
        object.__objectSignals__[signalIndex].push callback
        if !isPropertyNotifySignal and signalName != 'destroyed'
          # only required for "pure" signals, handled separately for properties in propertyUpdate
          # also note that we always get notified about the destroyed signal
          webChannel.exec
            type: QWebChannelMessageTypes.connectToSignal
            object: object.__id__
            signal: signalIndex
        return
      disconnect: (callback) ->
        if typeof callback != 'function'
          console.error 'Bad callback given to disconnect from signal ' + signalName + ' Type:' + typeof callback.toString()
          return
        object.__objectSignals__[signalIndex] = object.__objectSignals__[signalIndex] or []
        idx = object.__objectSignals__[signalIndex].indexOf(callback)
        if idx == -1
          console.error 'Cannot find connection of signal ' + signalName + ' to ' + callback.name
          return
        object.__objectSignals__[signalIndex].splice idx, 1
        if !isPropertyNotifySignal and object.__objectSignals__[signalIndex].length == 0
          # only required for "pure" signals, handled separately for properties in propertyUpdate
          webChannel.exec
            type: QWebChannelMessageTypes.disconnectFromSignal
            object: object.__id__
            signal: signalIndex
        return
    return

  ###*
  # Invokes all callbacks for the given signalname. Also works for property notify callbacks.
  ###

  invokeSignalCallbacks = (signalName, signalArgs) ->
    connections = object.__objectSignals__[signalName]
    if connections
      connections.forEach (callback) ->
        callback.apply callback, signalArgs
        return
    return

  addMethod = (methodData) ->
    methodName = methodData[0]
    methodIdx = methodData[1]

    object[methodName] = ->
      args = []
      callback = undefined
      i = 0
      while i < arguments.length
        if typeof arguments[i] == 'function'
          callback = arguments[i]
        else
          args.push arguments[i]
        ++i
      webChannel.exec {
        'type': QWebChannelMessageTypes.invokeMethod
        'object': object.__id__
        'method': methodIdx
        'args': args
      }, (response) ->
        if response != undefined
          result = object.unwrapQObject(response)
          if callback
            callback result
        return
      return

    return

  bindGetterSetter = (propertyInfo) ->
    propertyIndex = propertyInfo[0]
    propertyName = propertyInfo[1]
    notifySignalData = propertyInfo[2]
    # initialize property cache with current value
    # NOTE: if this is an object, it is not directly unwrapped as it might
    # reference other QObject that we do not know yet
    object.__propertyCache__[propertyIndex] = propertyInfo[3]
    if notifySignalData
      if notifySignalData[0] == 1
        # signal name is optimized away, reconstruct the actual name
        notifySignalData[0] = propertyName + 'Changed'
      addSignal notifySignalData, true
    Object.defineProperty object, propertyName,
      configurable: true
      get: ->
        propertyValue = object.__propertyCache__[propertyIndex]
        if propertyValue == undefined
          # This shouldn't happen
          console.warn 'Undefined value in property cache for property "' + propertyName + '" in object ' + object.__id__
        propertyValue
      set: (value) ->
        if value == undefined
          console.warn 'Property setter for ' + propertyName + ' called with undefined value!'
          return
        object.__propertyCache__[propertyIndex] = value
        webChannel.exec
          'type': QWebChannelMessageTypes.setProperty
          'object': object.__id__
          'property': propertyIndex
          'value': value
        return
    return

  @__id__ = name
  webChannel.objects[name] = this
  # List of callbacks that get invoked upon signal emission
  @__objectSignals__ = {}
  # Cache of all properties, updated when a notify signal is emitted
  @__propertyCache__ = {}
  object = this
  # ----------------------------------------------------------------------

  @unwrapQObject = (response) ->
    if response instanceof Array
      # support list of objects
      ret = new Array(response.length)
      i = 0
      while i < response.length
        ret[i] = object.unwrapQObject(response[i])
        ++i
      return ret
    if !response or !response['__QObject*__'] or response.id == undefined
      return response
    objectId = response.id
    if webChannel.objects[objectId]
      return webChannel.objects[objectId]
    if !response.data
      console.error 'Cannot unwrap unknown QObject ' + objectId + ' without data.'
      return
    qObject = new QObject(objectId, response.data, webChannel)
    qObject.destroyed.connect ->
      if webChannel.objects[objectId] == qObject
        delete webChannel.objects[objectId]
        # reset the now deleted QObject to an empty {} object
        # just assigning {} though would not have the desired effect, but the
        # below also ensures all external references will see the empty map
        # NOTE: this detour is necessary to workaround QTBUG-40021
        propertyNames = []
        for propertyName of qObject
          propertyNames.push propertyName
        for idx of propertyNames
          delete qObject[propertyNames[idx]]
      return
    # here we are already initialized, and thus must directly unwrap the properties
    qObject.unwrapProperties()
    qObject

  @unwrapProperties = ->
    for propertyIdx of object.__propertyCache__
      object.__propertyCache__[propertyIdx] = object.unwrapQObject(object.__propertyCache__[propertyIdx])
    return

  @propertyUpdate = (signals, propertyMap) ->
    # update property cache
    for propertyIndex of propertyMap
      propertyValue = propertyMap[propertyIndex]
      object.__propertyCache__[propertyIndex] = propertyValue
    for signalName of signals
      # Invoke all callbacks, as signalEmitted() does not. This ensures the
      # property cache is updated before the callbacks are invoked.
      invokeSignalCallbacks signalName, signals[signalName]
    return

  @signalEmitted = (signalName, signalArgs) ->
    invokeSignalCallbacks signalName, signalArgs
    return

  # ----------------------------------------------------------------------
  data.methods.forEach addMethod
  data.properties.forEach bindGetterSetter
  data.signals.forEach (signal) ->
    addSignal signal, false
    return
  for name of data.enums
    object[name] = data.enums[name]
  return

'use strict'
QWebChannelMessageTypes =
  signal: 1
  propertyUpdate: 2
  init: 3
  idle: 4
  debug: 5
  invokeMethod: 6
  connectToSignal: 7
  disconnectFromSignal: 8
  setProperty: 9
  response: 10

QWebChannel = (transport, initCallback) ->
  if typeof transport != 'object' or typeof transport.send != 'function'
    console.error 'The QWebChannel expects a transport object with a send function and onmessage callback property.' + ' Given is: transport: ' + typeof transport + ', transport.send: ' + typeof transport.send
    return
  channel = this
  @transport = transport

  @send = (data) ->
    if typeof data != 'string'
      data = JSON.stringify(data)
    channel.transport.send data
    return

  @transport.onmessage = (message) ->
    data = message.data
    if typeof data == 'string'
      data = JSON.parse(data)
    switch data.type
      when QWebChannelMessageTypes.signal
        channel.handleSignal data
      when QWebChannelMessageTypes.response
        channel.handleResponse data
      when QWebChannelMessageTypes.propertyUpdate
        channel.handlePropertyUpdate data
      else
        console.error 'invalid message received:', message.data
        break
    return

  @execCallbacks = {}
  @execId = 0

  @exec = (data, callback) ->
    if !callback
      # if no callback is given, send directly
      channel.send data
      return
    if channel.execId == Number.MAX_VALUE
      # wrap
      channel.execId = Number.MIN_VALUE
    if data.hasOwnProperty('id')
      console.error 'Cannot exec message with property id: ' + JSON.stringify(data)
      return
    data.id = channel.execId++
    channel.execCallbacks[data.id] = callback
    channel.send data
    return

  @objects = {}

  @handleSignal = (message) ->
    object = channel.objects[message.object]
    if object
      object.signalEmitted message.signal, message.args
    else
      console.warn 'Unhandled signal: ' + message.object + '::' + message.signal
    return

  @handleResponse = (message) ->
    if !message.hasOwnProperty('id')
      console.error 'Invalid response message received: ', JSON.stringify(message)
      return
    channel.execCallbacks[message.id] message.data
    delete channel.execCallbacks[message.id]
    return

  @handlePropertyUpdate = (message) ->
    for i of message.data
      data = message.data[i]
      object = channel.objects[data.object]
      if object
        object.propertyUpdate data.signals, data.properties
      else
        console.warn 'Unhandled property update: ' + data.object + '::' + data.signal
    channel.exec type: QWebChannelMessageTypes.idle
    return

  @debug = (message) ->
    channel.send
      type: QWebChannelMessageTypes.debug
      data: message
    return

  channel.exec { type: QWebChannelMessageTypes.init }, (data) ->
    `var objectName`
    for objectName of data
      object = new QObject(objectName, data[objectName], channel)
    # now unwrap properties, which might reference other registered objects
    for objectName of channel.objects
      channel.objects[objectName].unwrapProperties()
    if initCallback
      initCallback channel
    channel.exec type: QWebChannelMessageTypes.idle
    return
  return

#required for use with nodejs
if typeof module == 'object'
  module.exports = QWebChannel: QWebChannel