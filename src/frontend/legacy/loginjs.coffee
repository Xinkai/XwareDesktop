"use strict"
window.idocument=document.getElementsByTagName("iFrame")[0].contentDocument

class LoginHelper
    username=undefined
    username_text=undefined
    password=undefined
    password_text=undefined
    autologin=undefined
    login=undefined
    warn=undefined
    constructor: () ->
        xdpy.test("logining")
        xdpy.sigLogin.connect(@slotLogin)
        setTimeout(
            () ->
                username = idocument.getElementById("al_u")
                username_text=idocument.getElementById("al_u_l")
                password = idocument.getElementById("al_p")
                password_text=idocument.getElementById("al_p_l")
                autologin = idocument.getElementById("al_remember")
                login = idocument.getElementById("al_submit")
                warn=idocument.getElementById("al_warn")
                if not (username and password and autologin and login)
                    console.log("Cannot find username/password/autologin/login, retry in 1 sec.")
                else
                    xdpy.xdjsLoaded({
                        peerids: []
                        userid: null
                    })
            , 1000)  # wait for form

    slotLogin: (name, passwd) ->
        click_events=document.createEvent("MouseEvents")
        click_events.initEvent("click",true,false)
        url_temp=document.URL

        username_text.dispatchEvent(click_events)
        username.value =name
        password_text.dispatchEvent(click_events)
        password.value = passwd

        click_loop=setInterval(
            ()->
                if(idocument.title.includes("图形验证") or idocument.title.includes("滑动"))
                    alert("图片验证")
                    clearInterval click_loop
                    return
                if(warn.textContent.includes("密码错误"))
                    clearInterval click_loop
                    alert("密码错误! 请在设置中重新输入密码!")
                    return
                else if (warn.textContent.includes("请稍后再试") and warn.textContent.includes("登录操作过于频繁"))
                    clearInterval click_loop
                    alert("登陆失败,账号被限制登陆了,建议30分钟后再试")
                    return
                if(document.URL!=url_temp)
                    clearInterval click_loop
                login.click()
            ,2000)

    saveCredentials: () ->
        login.addEventListener("click",
            ()->
                username_value=username.value
                password_value=password.value
                if(username_value!="" and password_value!="")
                    xdpy.saveCredentials(username_value, password_value)
        )

window.onerror = (event, source, lineno, colno, error) ->
    xdpy.onJsError(event, source, lineno, colno, error)
    return false  # allow default handler

idocument.onreadystatechange = () ->
    if idocument.readyState is "complete"
        loginHelper = new LoginHelper()
idocument.onreadystatechange()
