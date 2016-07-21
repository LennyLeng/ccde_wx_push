# ccde_wx_push

这是CCDE公司微信公众号信息推送平台系统。<br>采用python + flask + redis + mariadb的架构实现。
mariadb实现数据持久化，利用redis的订阅发布模式实现跨微服务之间的消息同步
