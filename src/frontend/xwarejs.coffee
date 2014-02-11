"use strict"

class XwareJS
    constructor: () ->
        xdpy.sigCreateTasks.connect(@, @slotCreateTasks)
        xdpy.sigLogin.connect(@, @slotLogin)
        xdpy.sigActivateDevice.connect(@, @slotActivateDevice)
        xdpy.sigToggleFlashAvailability.connect(@, @slotToggleFlashAvailability)
        xdpy.xdjsLoaded()

        @bindOpenFile()

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

    slotLogin: (username, password) ->
        if $("#login-input-username").length > 0
            $("#login-input-username").val(username).blur()
            $("#login-input-password").val(password)

            setTimeout( ->
                $("#login-button").click()
            , 1500)

    slotToggleFlashAvailability: (available) ->
        App.set("system.flash", available)

    slotActivateDevice: () ->
        App.set("dialogs.addDownloader.show", true)

$ ->
    window.xdjs = new XwareJS()
