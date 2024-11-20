# 用法
首先修改配置文件`config.json`，内容大致如下
```json
{
    "targetClass" : [
        {
            "className" : "com.detective.utils.EncryptUtil", //目标类名
            "methodName" : [
                {
                    "name": "encryptPassword", //目标方法
                    "flag": false // 是否修改返回值
                },
                {
                    "name": "decryptPassword", //目标方法
                    "flag": true, // 是否修改返回值
                    "retVal": "123456" // 要修改的值
                }
            ]
        },
        {
            // 同上
        }
    ]
}
```
运行想要注入的jar包，java -jar -javaagent:agent路径=config路径 jar包（和其他运行项目所需的参数）
