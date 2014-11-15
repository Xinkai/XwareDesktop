"use strict"

class LoginHelper
    constructor: () ->
        xdpy.sigLogin.connect(@, @slotLogin)

        intervalId = setInterval(
            () =>
                @$username = document.getElementById("al_u")
                @$password = document.getElementById("al_p")
                @$autologin = document.getElementById("al_remember")
                @$login = document.getElementById("al_submit")

                if not (@$username and @$password and @$autologin and @$login)
                    console.log("Cannot find username/password/autologin/login, retry in 1 sec.")
                else
                    xdpy.xdjsLoaded({
                        peerids: []
                        userid: null
                    })
                    @bindSaveCredentials()
                    clearInterval intervalId
            , 1000)  # wait for form

    slotLogin: (username, password) ->
        @$username.value = username
        @$password.value = password

        interval_id = setInterval(
            () =>
                eventObj = document.createEvent("MouseEvents")
                eventObj.initEvent("click", true, false)
                @$login.dispatchEvent(eventObj)
                clearInterval interval_id
            , 1000)

    bindSaveCredentials: () =>
        @$login.addEventListener("click", () =>
            autologin = @$autologin.checked
            if not autologin
                return
            username = @$username.value
            password = @$password.value
            xdpy.saveCredentials(username, password)
        )

window.onerror = (event, source, lineno, colno, error) ->
    xdpy.onJsError(event, source, lineno, colno, error)
    return false  # allow default handler

document.onreadystatechange = () ->
    if document.readyState is "complete"
        window.loginHelper = new LoginHelper()
document.onreadystatechange()

null
