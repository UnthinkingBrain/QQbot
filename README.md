# 宿舍智能报修与AI助手系统

基于 NapCat QQ Bot 框架构建的宿舍消息处理系统。系统采用 WebSocket 事件驱动架构，实现群聊报修自动分流与私聊 AI 助手的双通道处理模式。

---

## 功能说明

### 群聊（报修系统）
系统对群消息进行自动分类识别，将宿舍相关问题归类为不同工单类型，并完成自动化处理：

- 自动识别报修类别（洗衣机、浴室、物业、水电等）
- 自动生成工单 ID
- 工单本地 YAML 持久化存储
- 优先级自动判断（urgent / normal / low）
- 相同问题短时间内自动合并，避免重复提交
- 根据类别自动路由到对应负责人

---

### 私聊（AI助手）
私聊模式提供独立的对话服务：

- 基于大模型的问答能力
- 按用户维度维护上下文记忆
- 支持多轮连续对话
- 不依赖工单系统，作为独立助手使用

---

## 系统结构

```

## NapCat QQ Bot  
↓  
WebSocket 事件接收  
↓  
消息路由层  
↓

## | 群聊处理 | 私聊处理 |  
| 工单系统 | AI助手 |

```
  ↓           ↓
```

YAML存储 对话记忆  
↓ ↓  
工单分发 模型回复

````

---

## 技术实现

- NapCat 作为 QQ 协议接入层
- WebSocket 用于事件通信
- 大模型用于分类与对话生成
- YAML 用于本地工单持久化
- 异步任务处理提高并发能力

---

## 环境依赖

```bash
pip install websockets openai pyyaml
````

---

## 环境变量

```bash
WS_URL=ws://<napcat-server>/ws?access_token=xxxx
NVIDIA_API_KEY=your_api_key
```

---

## 启动方式

```bash
python bot.py
```

---

## 工单数据结构

YAML 文件用于存储所有工单信息：

```yaml
1700000000000:
  category: property
  priority: urgent
  content: 厕所堵塞
  status: new
  time: 1700000000
```

---

## 分类规则

|类型|说明|
|---|---|
|washer|洗衣机、烘干机、洗鞋机|
|bathroom|浴室设备|
|property|堵塞、漏水、保洁问题|
|water|饮水机相关|
|hydropower|电力与空调费用问题|
|other|无法识别|

---

## 设计目标

系统用于宿舍场景下的消息自动处理与问题分发，核心目标包括：

- 减少人工分流成本
    
- 提升报修处理效率
    
- 统一问题记录与追踪
    
- 支持后续功能扩展
    

---

## 可扩展方向

- 工单状态流转（processing / done）
    
- SQLite 或数据库存储替代 YAML
    
- Web 管理接口
    
- AI 自动补全报修信息
    
- 报修数据统计分析模块
