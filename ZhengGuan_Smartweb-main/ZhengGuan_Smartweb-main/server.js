require('dotenv').config();
const express = require('express');
const axios = require('axios');
const app = express();

// 启用跨域资源共享（CORS），让前端能够访问
const cors = require('cors');
app.use(cors());

app.use(express.static('public'));

// 获取 conversation_id 的函数
async function getConversationId() {
    const options = {
        'method': 'POST',
        'url': 'https://qianfan.baidubce.com/v2/app/conversation',
        'headers': {
            'Content-Type': 'application/json',
            // 这里原来写死了密钥，现在改成读取.env变量
            'X-Appbuilder-Authorization': `Bearer ${process.env.QIANFAN_TOKEN}`
        },
        data: JSON.stringify({
            // app_id 也替换成环境变量
            "app_id": process.env.QIANFAN_APPID
        })
    };

    try {
        const response = await axios(options);
        console.log(response.data.conversation_id);
        return response.data.conversation_id;  // 返回 conversation_id
    } catch (error) {
        console.error('获取 conversation_id 失败:', error);
        throw error;
    }
}

app.get('/getAnswer', async (req, res) => {
    try {
        // 获取 conversation_id
        const conversationId = await getConversationId();

        const options = {
            'method': 'POST',
            'url': 'https://qianfan.baidubce.com/v2/app/conversation/runs',
            'headers': {
                'Content-Type': 'application/json',
                'X-Appbuilder-Authorization': `Bearer ${process.env.QIANFAN_TOKEN}`
            },
            data: JSON.stringify({
                "app_id": process.env.QIANFAN_APPID,
                "query": req.query.query || "你好",
                "conversation_id": conversationId,
                "stream": false
            })
        };

        const response = await axios(options);
        res.json({ answer: response.data.answer });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: '请求失败' });
    }
});

// 启动服务器
app.listen(3000, () => {
    console.log('Server is running on http://localhost:3000');
});