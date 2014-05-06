"use strict"

class XwareJS
    constructor: () ->
        xdpy.sigCreateTasks.connect(@, @slotCreateTasks)
        xdpy.sigCreateTaskFromTorrentFile.connect(@, @slotCreateTaskFromTorrentFile)
        xdpy.sigCreateTaskFromTorrentFileDone.connect(@, @slotCreateTaskFromTorrentFileDone)
        xdpy.sigLogin.connect(@, @slotLogin)
        xdpy.sigActivateDevice.connect(@, @slotActivateDevice)
        xdpy.sigToggleFlashAvailability.connect(@, @slotToggleFlashAvailability)

        @boundPeerId = false
        xdpy.sigNotifyPeerId.connect(@, @slotWaitToBindDeviceObserver)

        @bindDblclick()
        @bindContextMenu()
        @bindSaveCredentials()
        @bindMaskObserver()
        @bindTaskTabObserver()
        @fixDeviceShortName()

        result = {}
        if Data?
            result.peerids = (peerid for peerid of Data.downloader.all)
            result.userid = Data.session.userId
        else
            result.peerids = []
            result.userid = null
        xdpy.xdjsLoaded(result)

    log: (items...) ->
        xdpy.log(items)

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

    isShowingLocalDevice: () ->
        return @boundPeerId is Data.downloader.pid

    bindDblclick: () ->
        _this = @
        $("#task-list").on "dblclick", "div.rw_unit", (event) ->
            if not _this.isShowingLocalDevice()
                return
            tid = $(@).attr("data-tid")
            task = Data.task.all[tid]
            if task.stateText is "已完成"
                xdpy.systemOpen(task.path + task.name)
                event.preventDefault()
                event.stopImmediatePropagation()
                event.stopPropagation()

    bindContextMenu: () ->
        _this = @
        $("#task-list").on "contextmenu", "div.rw_unit", (event) ->
            if not _this.isShowingLocalDevice()
                return
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
            "attributeFilter": ["class"]
        })

    getDeviceIndex: (peerId) ->
        for i, item of Data.downloader.list
            if item.pid is peerId
                return i
        return NaN

    bindDeviceObserver: (boundPeerId) ->
        # prevent multiple binding
        if @boundPeerId
            return
        @boundPeerId = boundPeerId

        deviceIndex = @getDeviceIndex(boundPeerId)
        if (not isNaN(deviceIndex)) and (App.get("downloader.activedIndex") isnt deviceIndex)
            App.set("downloader.activedIndex", deviceIndex)

        @log "bindDeviceObserver"

        _online = Data.downloader.all[boundPeerId].online
        _logined = Data.downloader.all[boundPeerId].logined

        Object.defineProperty(Data.downloader.all[boundPeerId], "online", {
            get: () ->
                return _online
            set: (v) =>
                _online = v
                xdpy.slotSetOnline(v)

                console.log("set online", v)
        })

        Object.defineProperty(Data.downloader.all[boundPeerId], "logined", {
            get: () ->
                return _logined
            set: (v) =>
                _logined = v
                xdpy.slotSetLogined(v)

                console.log("set logined", v)
        })

        xdpy.slotSetOnline(_online)
        xdpy.slotSetLogined(_logined)

    slotWaitToBindDeviceObserver: (boundPeerId) ->
        # This method exists because the peerids are loaded by an ajax request,
        # when the network is a bit slow, peerids are delayed.
        # Using a setInterval to wait for the peerids being loaded is good enough.
        if Data?.downloader?
            # the right page
            intervalId = setInterval () =>
                if boundPeerId of Data.downloader.all
                    clearInterval(intervalId)
                    @bindDeviceObserver(boundPeerId)
            , 500

    bindTaskTabObserver: () ->
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

    fixDeviceShortName: () ->
        if Data?.downloader?.template?
            Data.downloader.template.item = Data.downloader.template.item.replace(/\{\{shortName\}\}/g, "{{name}}")

$ ->
    window.onerror = (event, source, lineno, colno, error) ->
        xdpy.onJsError(event, source, lineno, colno, error)
        return false  # allow default handler

    if (not window.MutationObserver) and window.WebKitMutationObserver
        window.MutationObserver = window.WebKitMutationObserver

    window.xdjs = new XwareJS()
