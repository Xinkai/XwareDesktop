"use strict"

class XwareJS
    constructor: () ->
        xdpy.sigCreateTasks.connect(@, @slotCreateTasks)
        xdpy.sigLogin.connect(@, @slotLogin)
        xdpy.sigActivateDevice.connect(@, @slotActivateDevice)
        xdpy.sigToggleFlashAvailability.connect(@, @slotToggleFlashAvailability)
        @bindDblclick()
        @bindContextMenu()
        @bindSaveCredentials()
        @bindMaskObserver()
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

    bindDblclick: () ->
        $("#task-list").on "dblclick", "div.rw_unit", (event) ->
            tid = $(@).attr("data-tid")
            task = Data.task.all[tid]
            if task.stateText is "已完成"
                xdpy.systemOpen(task.path + task.name)
                event.preventDefault()
                event.stopImmediatePropagation()
                event.stopPropagation()

    bindContextMenu: () ->
        $("#task-list").on "contextmenu", "div.rw_unit", (event) ->
            tid = $(@).attr("data-tid")
            task = Data.task.all[tid]

            $openDir = $("<li><a href='javascript:void(0)'>打开所在文件夹</a></li>")
            $openDir.on "click", () ->
                xdpy.systemOpen(task.path)

            $cmenu = $("div#cmenu.flo_wrap > ul.flo_ul")
            $cmenu.prepend($openDir)

            if task.stateText is "已完成"
                $open = $("<li><a href='javascript:void(0)'>打开</a></li>")
                $open.on "click", () ->
                    xdpy.systemOpen(task.path + task.name)
                $cmenu.prepend($open)

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

    bindMaskObserver: () ->
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
            "aattributeFilter": ["class"]
        })



$ ->
    window.xdjs = new XwareJS()
