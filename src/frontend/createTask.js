"use strict";

$(function() {
    App._binder._bindings["dialogs.createTask.show"][0](true);

    var $createTaskUrl = $("#d-create-task-url");
    var taskUrl = $createTaskUrl.val();
    $createTaskUrl.val("http://www.baidu.com/robots.txt" + "\n" + taskUrl);
    $createTaskUrl.keyup();
});