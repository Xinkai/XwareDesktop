"use strict"

class XwareJS
    constructor: () ->
        xdpy.sigCreateTasks.connect(@, @slotCreateTasks)
        xdpy.sigLogin.connect(@, @slotLogin)
        xdpy.xdjsLoaded()

    slotCreateTasks: (tasks) ->
        App._binder._bindings["dialogs.createTask.show"][0](true)

        $createTaskUrl = $("#d-create-task-url")
        taskUrl = $createTaskUrl.val()
        $createTaskUrl.val(tasks + "\n" + taskUrl)
        $createTaskUrl.keyup()

        $createTaskUrl.get(0).focus()
        xdpy.requestFocus()

    slotLogin: (username, password) ->
        $("#login-input-username").val(username).blur()
        $("#login-input-password").val(password)

        setTimeout( ->
            $("#login-button").click()
        , 1500)

$ ->
    window.xdjs = new XwareJS()
