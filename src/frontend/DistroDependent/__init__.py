# -*- coding: utf-8 -*-

# Xware Desktop针对各个发行版的不同，根据此文件分别应对
# 打包人员应按情况适当替换以下内容

### 计划任务
# 电源控制的用户组，必须在此组内才能以非root身份控制开关机操作
SCHEDULER_POWERGROUP = "power"

## 若以下4种关机模式发行版不支持，可以填写空字符串
# 关机命令
SCHEDULER_POWEROFF_COMMAND = "systemctl poweroff"

# 混合模式休眠命令
SCHEDULER_HYBRIDSLEEP_COMMAND = "systemctl hybrid-sleep"

# 休眠到磁盘（也叫休眠）命令
SCHEDULER_HIBERNATE_COMMAND = "systemctl hibernate"

# 休眠到内存（也叫睡眠）命令
SCHEDULER_SUSPEND_COMMAND = "systemctl suspend"

