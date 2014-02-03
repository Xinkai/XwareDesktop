"use strict";

$(function() {
    $("#login-input-username").val("{username}").blur();
    $("#login-input-password").val("{password}");

    setTimeout(function() {
        $("#login-button").click();
    }, 1000);
});