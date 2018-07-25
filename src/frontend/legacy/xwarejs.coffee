"use strict"

class XwareJS
    boundPeerId = false
    constructor: () ->
        xdpy.test("logined")
        xdpy.sigCreateTask.connect(@slotCreateTask)
        xdpy.sigCreateTaskFromTorrentFile.connect(@slotCreateTaskFromTorrentFile)
        xdpy.sigCreateTaskFromTorrentFileDone.connect(@slotCreateTaskFromTorrentFileDone)
        xdpy.sigActivateDevice.connect(@slotActivateDevice)
        xdpy.sigToggleFlashAvailability.connect(@slotToggleFlashAvailability)

        #window.bindDeviceObserver=@bindDeviceObserver
        #window.getDeviceIndex=@getDeviceIndex
        #window.writeLog=@writeLog

        xdpy.sigNotifyPeerId.connect(@slotWaitToBindDeviceObserver)

        bindDblclick()
        bindContextMenu()
        bindMaskObserver()
        bindTaskTabObserver()
        fixDeviceShortName()

        result = {}
        if Data?
            result.peerids = (peerid for peerid of Data.downloader.all)
            result.userid = Data.session.userId
        else
            result.peerids = []
            result.userid = null
        xdpy.xdjsLoaded(result)

    writeLog=(items...) ->
        xdpy.log(items)

    isShowingLocalDevice=() ->
        return boundPeerId is Data.downloader.pid

    bindDblclick=() ->
        $("#task-list").on "dblclick", "div.rw_unit", (event) ->
            if not isShowingLocalDevice()
                return
            tid = $(@).attr("data-tid")
            task = Data.task.all[tid]
            if task.stateText is "已完成"
                if task.path
                    xdpy.systemOpen(task.path + task.name)
                else
                    console.error "No Task Path"
                event.preventDefault()
                event.stopImmediatePropagation()
                event.stopPropagation()

    bindContextMenu=() ->
        $("#task-list").on "contextmenu", "div.rw_unit", (event) ->
            if not isShowingLocalDevice()
                return
            tid = $(@).attr("data-tid")
            task = Data.task.all[tid]
            $openDir = $("<li><a href='javascript:void(0)'>在文件夹中显示</a></li>")
            $openDir.on "click", () ->
                #if task.path
                    xdpy.systemViewOneFile(task.path + task.name)
                #else
                    #console.error "No Task Path"
            $cmenu = $("div#cmenu.flo_wrap > ul.flo_ul")
            $cmenu.prepend($openDir)

            if task.stateText is "已完成"
                $open = $("<li><a href='javascript:void(0)'>打开</a></li>")
                $open.on "click", () ->
                    if task.path
                        xdpy.systemOpen(task.path + task.name)
                    else
                        console.error "No Task Path"
                $cmenu.prepend($open)

    slotCreateTask: (task) ->
        App.set("dialogs.createTask.show", true)
        $createTaskUrl = $("#d-create-task-url")
        $createTaskUrl.val(task)
        $createTaskUrl.keyup()

        $createTaskUrl.get(0).focus()
        xdpy.requestFocus()

    slotCreateTaskFromTorrentFile: () ->
        App.set("dialogs.createTask.show", true)
        $(".faked").addClass("faked-toggle").removeClass("faked")
        $inputFile = $("#d-create-task-bt-file")
        $inputFile.focus()
        xdpy.slotClickBtButton()

    slotCreateTaskFromTorrentFileDone: () ->
        $(".faked-toggle").remove("faked-toggle").addClass("faked")

    slotToggleFlashAvailability: (available) ->
        App.set("system.flash", available)

    slotActivateDevice: (code) ->
        App.set("dialogs.addDownloader.show", true)

        $types = $("#d-add-downloader-types > li")
        # choose NAS
        $("> a[title$='NAS']", $types).click()
        # hide other types
        $types.not(":has(a[title$='NAS'])").hide()

        $panel = $("#d-add-downloader-panels > div.pop_addd_unit:not(.hidden)")
        # replace text
        $("> p", $panel).html("您需要激活后使用Xware Desktop。<br />激活码已经试着自动为您获取并填写，点击激活后稍等片刻即可。")
        # focus code input
        input = $("input.sel_inptxt", $panel).get(0)
        $(input).val(code).blur().trigger('input')
        input.focus()

        # refresh the page 5 seconds after 激活 btn is clicked
        $activateBtn = $(".btn_inp", $panel)
        $activateBtn.on "click", () ->
            setTimeout () ->
                location.reload(true)
            , 5000

    bindMaskObserver=() ->
        mask = document.getElementById("mask")
        maskon = false
        if not mask
            return
        xdpy.slotMaskOnOffChanged(false)

        observer = new MutationObserver () ->
            maskon_new = "hidden" not in mask.classList
            if maskon_new isnt maskon
                maskon = maskon_new
                xdpy.slotMaskOnOffChanged(maskon)

        observer.observe(mask, {
            "childList": false
            "attributes": true
            "characterData": false
            "subtree": false
            "attributeOldValue": false
            "characterDataOldValue": false
            "attributeFilter": ["class"]
        })

    getDeviceIndex=(peerId) ->
        for i, item of Data.downloader.list
            if item.pid is peerId
                return i
        return NaN

    bindDeviceObserver=(bpid) ->

        # prevent multiple binding
        if boundPeerId
            return
        boundPeerId = bpid

        deviceIndex = getDeviceIndex(bpid)

        if (not isNaN(deviceIndex)) and (App.get("downloader.activedIndex") isnt deviceIndex)
            App.set("downloader.activedIndex", deviceIndex)

        writeLog "bindDeviceObserver"

        _online = Data.downloader.all[bpid].online
        _logined = Data.downloader.all[bpid].logined

        Object.defineProperty(Data.downloader.all[bpid], "online", {
            get: () ->
                return _online
            set: (v) =>
                _online = v
                xdpy.slotSetOnline(v)

                console.log("set online", v)
        })

        Object.defineProperty(Data.downloader.all[bpid], "logined", {
            get: () ->
                return _logined
            set: (v) =>
                _logined = v
                xdpy.slotSetLogined(v)

                console.log("set logined", v)
        })

        if typeof _online is "number"
            xdpy.slotSetOnline(_online)
        if typeof _logined is "number"
            xdpy.slotSetLogined(_logined)
        return

    slotWaitToBindDeviceObserver: (bpid) ->
        # This method exists because the peerids are loaded by an ajax request,
        # when the network is a bit slow, peerids are delayed.
        # Using a setInterval to wait for the peerids being loaded is good enough.
        if Data?.downloader?
            # the right page
            intervalId = setInterval () =>
                if bpid of Data.downloader.all
                    clearInterval(intervalId)
                    bindDeviceObserver(bpid)
            , 500
        return

    bindTaskTabObserver=() ->
        taskSidebar = document.getElementById("task-sidebar")
        if not taskSidebar
            return

        observer = new MutationObserver (mutations) =>
            mutations.forEach (m) =>
                if "on" in m.target.classList and not m.oldValue
                    $("#task-list").attr("data-showtype", m.target.getAttribute("data-value"))

        observer.observe(taskSidebar, {
            "childList": false
            "attributes": true
            "characterData": false
            "subtree": true
            "attributeOldValue": true
            "characterDataOldValue": false
            "attributeFilter": ['class']
        })
        return

    fixDeviceShortName=() ->
        if Data?.downloader?.template?
            Data.downloader.template.item = Data.downloader.template.item.replace(/\{\{shortName\}\}/g, "{{name}}")
        return
window.onerror = (event, source, lineno, colno, error) ->
        xdpy.onJsError(event, source, lineno, colno, error)
        return false  # allow default handler

if (not window.MutationObserver) and window.WebKitMutationObserver
    window.MutationObserver = window.WebKitMutationObserver
document.onreadystatechange = () ->
    if document.readyState is "complete"
        window.xdjs = new XwareJS()
document.onreadystatechange()

# fix issue 64, by making Qt not cast the last statement's return value into a Qt type.
