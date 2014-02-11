"use strict"

class XwareJS
    constructor: () ->
        xdpy.sigCreateTasks.connect(@, @slotCreateTasks)
        xdpy.sigLogin.connect(@, @slotLogin)
        xdpy.sigActivateDevice.connect(@, @slotActivateDevice)
        xdpy.sigToggleFlashAvailability.connect(@, @slotToggleFlashAvailability)
        @bindOpenFile()
        @bindSaveCredentials()
        xdpy.xdjsLoaded()

    slotLogin: (username, password) ->
        $username = $("#login-input-username")
        $password = $("#login-input-password")
        if $username.length > 0
            $username.val(username).blur()
            $password.val(password).blur()

            interval_id = setInterval(
                () ->
                    if (Login.login.username is $username.val()) and (Login.login.verifyCode?.length > 0)
                        xdpy.log "tried to click"
                        $("#login-button").click()
                        clearInterval interval_id
                , 1000)

    bindSaveCredentials: () ->
        # shit, whoever did this spelled 'remember' wrong! if they fix it it'll break this
        $autologin = $("#login-remenber-0")
        if $autologin.length is 0
            return

        $username = $("#login-input-username")
        $password = $("#login-input-password")

        $("#login-button").click ->
            autologin = $autologin.prop("checked")
            if not autologin
                return
            username = $username.val()
            password = $password.val()
            xdpy.saveCredentials(username, password)

    bindOpenFile: () ->
        $("#task-list").on "dblclick", "div.rw_unit", (event) ->
            tid = $(@).attr("data-tid")
            task = Data.task.all[tid]
            if task.stateText is "已完成"
                xdpy.systemOpen(task.path + task.name)
                event.preventDefault()
                event.stopImmediatePropagation()
                event.stopPropagation()

    slotCreateTasks: (tasks) ->
        App.set("dialogs.createTask.show", true)

        $createTaskUrl = $("#d-create-task-url")
        tasks = tasks.join("\n")
        taskUrl = $createTaskUrl.val()
        $createTaskUrl.val(tasks + "\n" + taskUrl)
        $createTaskUrl.keyup()

        $createTaskUrl.get(0).focus()
        xdpy.requestFocus()



    slotToggleFlashAvailability: (available) ->
        App.set("system.flash", available)

    slotActivateDevice: () ->
        App.set("dialogs.addDownloader.show", true)

$ ->
    window.xdjs = new XwareJS()
