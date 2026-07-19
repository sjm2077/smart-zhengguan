<template>
  <div class="tree-hole">
    <div class="page-header">
      <h2>校园树洞</h2>
      <p>匿名分享，自由发声，温暖互助</p>
    </div>

    <div class="tab-nav">
      <button 
        v-for="tab in tabs" 
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
      </button>
    </div>

    <div class="content-area">
      <!-- 心情分享 -->
      <div v-if="activeTab === 'mood'" class="mood-section">
        <div class="post-card create-post">
          <div class="post-header">
            <span class="avatar-mask">👻</span>
            <span class="anonymous-tag">匿名发布</span>
          </div>
          <textarea 
            v-model="newPost.content" 
            placeholder="今天心情如何？分享你的故事..."
            class="post-input"
          ></textarea>
          <div class="mood-tags">
            <button 
              v-for="mood in moodTags" 
              :key="mood"
              :class="['mood-tag', { selected: newPost.mood === mood }]"
              @click="newPost.mood = mood"
            >
              {{ mood }}
            </button>
          </div>
          <button class="publish-btn" @click="publishPost">
            <span>📤</span> 发布
          </button>
        </div>

        <div class="posts-list">
          <div v-for="post in moodPosts" :key="post.id" class="post-card">
            <div class="post-header">
              <span class="avatar-mask">{{ post.avatar }}</span>
              <span class="post-time">{{ post.time }}</span>
              <span class="mood-badge" :class="post.moodType">{{ post.mood }}</span>
            </div>
            <div class="post-content">{{ post.content }}</div>
            <div class="post-actions">
              <button class="action-btn" @click="likePost(post)">
                <span>❤️</span> {{ post.likes }}
              </button>
              <button class="action-btn" @click="comfortPost(post)">
                <span>🤗</span> {{ post.comforts }}
              </button>
              <button class="action-btn" @click="showComments(post)">
                <span>💬</span> {{ post.comments }}
              </button>
            </div>
            <div v-if="post.showComments" class="comments-section">
              <div v-for="comment in post.commentList" :key="comment.id" class="comment-item">
                <span class="comment-avatar">{{ comment.avatar }}</span>
                <span class="comment-text">{{ comment.text }}</span>
              </div>
              <input 
                v-model="post.newComment" 
                placeholder="说点什么安慰TA..."
                class="comment-input"
                @keyup.enter="addComment(post)"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 吐槽好差评 -->
      <div v-if="activeTab === 'review'" class="review-section">
        <div class="review-categories">
          <button 
            v-for="cat in reviewCategories" 
            :key="cat.key"
            :class="['cat-btn', { active: reviewCategory === cat.key }]"
            @click="reviewCategory = cat.key"
          >
            <span class="cat-icon">{{ cat.icon }}</span>
            {{ cat.label }}
          </button>
        </div>

        <div class="publish-card">
          <div class="publish-title">📢 发布吐槽/好评</div>
          <div class="publish-row">
            <select v-model="newReview.category" class="publish-select">
              <option value="food">食堂</option>
              <option value="dorm">宿舍</option>
              <option value="library">图书馆</option>
              <option value="facility">设施</option>
            </select>
            <input v-model="newReview.target" placeholder="评价对象（如：一食堂二楼）" class="publish-input" />
          </div>
          <div class="publish-row">
            <div class="rating-picker">
              <span v-for="n in 5" :key="n" :class="['star-picker', { active: n <= newReview.rating }]" @click="newReview.rating = n">⭐</span>
            </div>
          </div>
          <textarea v-model="newReview.content" placeholder="说说你的体验..." class="publish-textarea"></textarea>
          <div class="publish-footer">
            <div class="tag-picker">
              <span v-for="tag in reviewTagOptions" :key="tag" :class="['pick-tag', { selected: newReview.tags.includes(tag) }]" @click="toggleReviewTag(tag)">{{ tag }}</span>
            </div>
            <button class="publish-submit" @click="publishReview">发布</button>
          </div>
        </div>

        <div class="review-list">
          <div v-for="review in filteredReviews" :key="review.id" class="review-card">
            <div class="review-header">
              <span class="review-avatar">🎭</span>
              <span class="review-target">{{ review.target }}</span>
              <div class="rating-stars">
                <span v-for="n in 5" :key="n" :class="['star', { filled: n <= review.rating }]">⭐</span>
              </div>
            </div>
            <div class="review-content">{{ review.content }}</div>
            <div class="review-tags">
              <span v-for="tag in review.tags" :key="tag" class="review-tag">{{ tag }}</span>
            </div>
            <div class="review-footer">
              <span class="review-time">{{ review.time }}</span>
              <span class="review-likes">👍 {{ review.likes }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 暖心鼓励 -->
      <div v-if="activeTab === 'warm'" class="warm-section">
        <div class="warm-wall">
          <div v-for="item in warmItems" :key="item.id" class="warm-card" :class="item.type">
            <div class="warm-content">
              <span class="warm-quote">"{{ item.quote }}"</span>
              <span class="warm-author">—— {{ item.author }}</span>
            </div>
            <div class="warm-stats">
              <span>🔥 {{ item.fires }}</span>
              <span>🌈 {{ item.rainbows }}</span>
            </div>
          </div>
        </div>

        <div class="add-warm">
          <textarea 
            v-model="newWarm.content" 
            placeholder="写下你想送给大家的温暖话语..."
            class="warm-input"
          ></textarea>
          <button class="warm-btn" @click="addWarm">
            <span>🌟</span> 发送温暖
          </button>
        </div>
      </div>

      <!-- 课程评价 -->
      <div v-if="activeTab === 'course'" class="course-section">
        <div class="course-search">
          <input 
            v-model="courseSearch" 
            placeholder="搜索课程名称或教师..."
            class="search-input"
          />
        </div>

        <div class="publish-card">
          <div class="publish-title">📝 发布课程评价</div>
          <div class="publish-row">
            <input v-model="newCourseEval.courseName" placeholder="课程名称" class="publish-input" style="flex:1" />
            <input v-model="newCourseEval.teacher" placeholder="授课教师" class="publish-input" style="flex:1" />
          </div>
          <div class="publish-row">
            <div class="rating-picker">
              <span v-for="n in 5" :key="n" :class="['star-picker', { active: n <= newCourseEval.rating }]" @click="newCourseEval.rating = n">⭐</span>
            </div>
          </div>
          <textarea v-model="newCourseEval.content" placeholder="分享你的学习体验..." class="publish-textarea"></textarea>
          <div class="publish-footer">
            <div class="tag-picker">
              <span v-for="tag in courseTagOptions" :key="tag" :class="['pick-tag', { selected: newCourseEval.tags.includes(tag) }]" @click="toggleCourseTag(tag)">{{ tag }}</span>
            </div>
            <button class="publish-submit" @click="publishCourseEval">发布</button>
          </div>
        </div>

        <div class="course-list">
          <div v-for="course in filteredCourses" :key="course.id" class="course-card">
            <div class="course-header">
              <div class="course-info">
                <h4 class="course-name">{{ course.name }}</h4>
                <span class="course-teacher">{{ course.teacher }}</span>
              </div>
              <div class="course-rating">
                <span class="avg-rating">{{ course.avgRating }}</span>
                <div class="rating-bar">
                  <div class="rating-fill" :style="{ width: (course.avgRating / 5 * 100) + '%' }"></div>
                </div>
              </div>
            </div>
            <div class="course-tags">
              <span v-for="tag in course.tags" :key="tag" class="course-tag">{{ tag }}</span>
            </div>
            <div class="course-stats">
              <span>📚 {{ course.evals }}条评价</span>
              <span>👥 {{ course.students }}人</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 课程互助 -->
      <div v-if="activeTab === 'help'" class="help-section">
        <div class="help-types">
          <button 
            v-for="type in helpTypes" 
            :key="type.key"
            :class="['type-btn', { active: helpType === type.key }]"
            @click="helpType = type.key"
          >
            <span>{{ type.icon }}</span> {{ type.label }}
          </button>
        </div>

        <div class="help-list">
          <div v-for="item in filteredHelps" :key="item.id" class="help-card">
            <div class="help-header">
              <span class="help-avatar">{{ item.avatar }}</span>
              <span class="help-type-tag" :class="item.type">{{ item.typeLabel }}</span>
              <span class="help-course">{{ item.course }}</span>
            </div>
            <div class="help-content">{{ item.content }}</div>
            <div class="help-footer">
              <span class="help-time">{{ item.time }}</span>
              <button class="help-action" @click="offerHelp(item)">
                <span>🙋</span> 我来帮忙
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 比赛组队 -->
      <div v-if="activeTab === 'team'" class="team-section">
        <div class="team-filters">
          <select v-model="teamFilter.type" class="filter-select">
            <option value="">全部类型</option>
            <option value="competition">竞赛组队</option>
            <option value="project">项目合作</option>
            <option value="study">学习小组</option>
            <option value="sports">运动搭子</option>
          </select>
          <select v-model="teamFilter.status" class="filter-select">
            <option value="">全部状态</option>
            <option value="recruiting">招募中</option>
            <option value="full">已满员</option>
            <option value="ongoing">进行中</option>
          </select>
        </div>

        <div class="team-list">
          <div v-for="team in filteredTeams" :key="team.id" class="team-card">
            <div class="team-header">
              <span class="team-avatar">{{ team.avatar }}</span>
              <span class="team-title">{{ team.title }}</span>
              <span class="team-status" :class="team.status">{{ team.statusLabel }}</span>
            </div>
            <div class="team-info">
              <span class="team-type">{{ team.typeLabel }}</span>
              <span class="team-members">👥 {{ team.current }}/{{ team.max }}人</span>
            </div>
            <div class="team-desc">{{ team.description }}</div>
            <div class="team-requirements">
              <span v-for="req in team.requirements" :key="req" class="req-tag">{{ req }}</span>
            </div>
            <div class="team-footer">
              <span class="team-time">{{ team.deadline }}</span>
              <button class="team-join" :disabled="team.status === 'full'" @click="joinTeam(team)">
                <span>✨</span> 申请加入
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 新闻播报 -->
      <div v-if="activeTab === 'news'" class="news-section">
        <div class="news-list">
          <a v-for="news in newsItems" :key="news.id" :href="news.link" target="_blank" class="news-card" :class="news.category">
            <div class="news-image">
              <span class="news-icon">{{ news.icon }}</span>
            </div>
            <div class="news-content">
              <span class="news-category-tag">{{ news.categoryLabel }}</span>
              <h4 class="news-title">{{ news.title }}</h4>
              <p class="news-summary">{{ news.summary }}</p>
              <div class="news-footer">
                <span class="news-source">{{ news.source }}</span>
                <span class="news-time">{{ news.time }}</span>
                <span class="news-views">👁️ {{ news.views }}</span>
              </div>
            </div>
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const activeTab = ref('mood')
const tabs = [
  { key: 'mood', label: '心情分享', icon: '💭' },
  { key: 'review', label: '吐槽好评', icon: '📢' },
  { key: 'warm', label: '暖心鼓励', icon: '🌟' },
  { key: 'course', label: '课程评价', icon: '📚' },
  { key: 'help', label: '课程互助', icon: '🤝' },
  { key: 'team', label: '比赛组队', icon: '👥' },
  { key: 'news', label: '新闻播报', icon: '📰' }
]

// 心情分享
const moodTags = ['开心', '平静', '焦虑', '沮丧', '兴奋', '感动']
const newPost = ref({ content: '', mood: '' })
const moodPosts = ref([
  { id: 1, avatar: '👻', time: '10分钟前', mood: '焦虑', moodType: 'negative', content: '最近论文进度很慢，导师催了好几次，压力有点大...', likes: 23, comforts: 15, comments: 8, showComments: false, newComment: '', commentList: [{ id: 1, avatar: '🤗', text: '加油！一步一步来，相信你能完成的！' }] },
  { id: 2, avatar: '🎉', time: '30分钟前', mood: '开心', moodType: 'positive', content: '终于拿到了心仪公司的offer！四年的努力终于有了回报，感谢所有帮助过我的人！', likes: 156, comforts: 89, comments: 42, showComments: false, newComment: '', commentList: [] },
  { id: 3, avatar: '🌙', time: '1小时前', mood: '平静', moodType: 'neutral', content: '今晚在图书馆看书，窗外月光很美。虽然学习很累，但偶尔的小确幸让人心安。', likes: 67, comforts: 32, comments: 18, showComments: false, newComment: '', commentList: [] }
])

const publishPost = () => {
  if (!newPost.value.content.trim()) return
  moodPosts.value.unshift({
    id: Date.now(),
    avatar: '👻',
    time: '刚刚',
    mood: newPost.value.mood || '平静',
    moodType: ['开心', '兴奋', '感动'].includes(newPost.value.mood) ? 'positive' : ['焦虑', '沮丧'].includes(newPost.value.mood) ? 'negative' : 'neutral',
    content: newPost.value.content,
    likes: 0,
    comforts: 0,
    comments: 0,
    showComments: false,
    newComment: '',
    commentList: []
  })
  newPost.value = { content: '', mood: '' }
}

const likePost = (post) => post.likes++
const comfortPost = (post) => post.comforts++
const showComments = (post) => post.showComments = !post.showComments
const addComment = (post) => {
  if (!post.newComment.trim()) return
  post.commentList.push({ id: Date.now(), avatar: '🤗', text: post.newComment })
  post.comments++
  post.newComment = ''
}

// 吐槽好评
const reviewCategory = ref('all')
const reviewCategories = [
  { key: 'all', label: '全部', icon: '📋' },
  { key: 'food', label: '食堂', icon: '🍜' },
  { key: 'dorm', label: '宿舍', icon: '🏠' },
  { key: 'library', label: '图书馆', icon: '📚' },
  { key: 'facility', label: '设施', icon: '🏫' }
]

const reviews = ref([
  { id: 1, category: 'food', target: '一食堂二楼川菜窗口', rating: 4, content: '辣子鸡做得不错，分量也够，阿姨态度好。就是有时候排队太久。', tags: ['分量足', '味道好', '排队久'], time: '2小时前', likes: 45 },
  { id: 2, category: 'library', target: '图书馆三楼自习区', rating: 5, content: '环境很好，安静舒适，空调给力。座位预约系统也很方便。', tags: ['环境好', '安静', '座位系统'], time: '3小时前', likes: 78 },
  { id: 3, category: 'dorm', target: 'A栋宿舍楼', rating: 3, content: '网络经常断，洗澡水有时候不热。但位置好，离教学楼近。', tags: ['位置好', '网络差', '洗澡问题'], time: '5小时前', likes: 23 },
  { id: 4, category: 'facility', target: '体育馆羽毛球馆', rating: 4, content: '场地宽敞，设施齐全，预约方便。周末人比较多需要提前预约。', tags: ['设施齐全', '场地好', '需预约'], time: '1天前', likes: 56 }
])

const filteredReviews = computed(() => {
  if (reviewCategory.value === 'all') return reviews.value
  return reviews.value.filter(r => r.category === reviewCategory.value)
})

// 发布吐槽
const newReview = ref({ category: 'food', target: '', rating: 5, content: '', tags: [] })
const reviewTagOptions = ['分量足', '味道好', '排队久', '环境好', '设施差', '服务好', '价格实惠', '推荐', '不推荐']
const toggleReviewTag = (tag) => {
  const idx = newReview.value.tags.indexOf(tag)
  if (idx > -1) newReview.value.tags.splice(idx, 1)
  else if (newReview.value.tags.length < 3) newReview.value.tags.push(tag)
}
const publishReview = () => {
  if (!newReview.value.target.trim() || !newReview.value.content.trim()) return
  reviews.value.unshift({
    id: Date.now(),
    category: newReview.value.category,
    target: newReview.value.target,
    rating: newReview.value.rating,
    content: newReview.value.content,
    tags: [...newReview.value.tags],
    time: '刚刚',
    likes: 0
  })
  newReview.value = { category: 'food', target: '', rating: 5, content: '', tags: [] }
}

// 暖心鼓励
const warmItems = ref([
  { id: 1, type: 'quote', quote: '你今天的努力，是幸运的伏笔。当下的付出，是明日的花开。', author: '匿名温暖者', fires: 156, rainbows: 89 },
  { id: 2, type: 'encourage', quote: '不要因为走得太远，而忘记为什么出发。', author: '一位学长', fires: 234, rainbows: 178 },
  { id: 3, type: 'story', quote: '去年考研失败的我，今年终于上岸了。所以，永远不要放弃希望！', author: '上岸的鱼', fires: 567, rainbows: 423 }
])

const newWarm = ref({ content: '' })
const addWarm = () => {
  if (!newWarm.value.content.trim()) return
  warmItems.value.unshift({
    id: Date.now(),
    type: 'quote',
    quote: newWarm.value.content,
    author: '匿名温暖者',
    fires: 0,
    rainbows: 0
  })
  newWarm.value.content = ''
}

// 课程评价
const courseSearch = ref('')
const courses = ref([
  { id: 1, name: '行政管理学', teacher: '张明辉教授', avgRating: 4.8, tags: ['干货满满', '互动性强', '考核合理'], evals: 56, students: 120 },
  { id: 2, name: '政治学原理', teacher: '王教授', avgRating: 4.5, tags: ['理论扎实', '作业适中', '推荐选修'], evals: 42, students: 85 },
  { id: 3, name: '公共政策分析', teacher: '李教授', avgRating: 4.2, tags: ['案例分析多', '小组作业', '需要预习'], evals: 38, students: 90 },
  { id: 4, name: '统计学方法', teacher: '陈教授', avgRating: 4.6, tags: ['实用性强', '难度适中', '考试开卷'], evals: 45, students: 75 }
])

const filteredCourses = computed(() => {
  if (!courseSearch.value.trim()) return courses.value
  return courses.value.filter(c => 
    c.name.includes(courseSearch.value) || c.teacher.includes(courseSearch.value)
  )
})

// 发布课程评价
const newCourseEval = ref({ courseName: '', teacher: '', rating: 5, content: '', tags: [] })
const courseTagOptions = ['干货满满', '互动性强', '考核合理', '理论扎实', '作业适中', '案例分析多', '小组作业', '推荐选修', '难度适中', '实用性强']
const toggleCourseTag = (tag) => {
  const idx = newCourseEval.value.tags.indexOf(tag)
  if (idx > -1) newCourseEval.value.tags.splice(idx, 1)
  else if (newCourseEval.value.tags.length < 3) newCourseEval.value.tags.push(tag)
}
const publishCourseEval = () => {
  if (!newCourseEval.value.courseName.trim() || !newCourseEval.value.content.trim()) return
  courses.value.unshift({
    id: Date.now(),
    name: newCourseEval.value.courseName,
    teacher: newCourseEval.value.teacher || '待确认',
    avgRating: newCourseEval.value.rating,
    tags: [...newCourseEval.value.tags],
    evals: 1,
    students: 0
  })
  newCourseEval.value = { courseName: '', teacher: '', rating: 5, content: '', tags: [] }
}

// 课程互助
const helpType = ref('all')
const helpTypes = [
  { key: 'all', label: '全部', icon: '📋' },
  { key: 'question', label: '答疑解惑', icon: '❓' },
  { key: 'material', label: '资料分享', icon: '📎' },
  { key: 'study', label: '学习组队', icon: '👥' }
]

const helpItems = ref([
  { id: 1, type: 'question', typeLabel: '答疑解惑', avatar: '🤔', course: '行政管理学', content: '请问有人能解释一下行政权力的三个维度吗？书上讲得有点抽象。', time: '20分钟前', helped: false },
  { id: 2, type: 'material', typeLabel: '资料分享', avatar: '📎', course: '政治学原理', content: '整理了一份政治学重点笔记，需要的同学可以私信我获取PDF。', time: '1小时前', helped: false },
  { id: 3, type: 'study', typeLabel: '学习组队', avatar: '👥', course: '统计学方法', content: '有没有同学想一起学习统计学？每周两次图书馆自习，互相监督。', time: '2小时前', helped: false }
])

const filteredHelps = computed(() => {
  if (helpType.value === 'all') return helpItems.value
  return helpItems.value.filter(h => h.type === helpType.value)
})

const offerHelp = (item) => {
  alert('已发送帮忙意向，请等待对方回复！')
}

// 比赛组队
const teamFilter = ref({ type: '', status: '' })
const teams = ref([
  { id: 1, type: 'competition', typeLabel: '竞赛组队', title: '互联网+创新创业大赛', status: 'recruiting', statusLabel: '招募中', current: 2, max: 5, description: '寻找有技术背景和设计能力的队友，项目方向：智慧校园平台。', requirements: ['有技术开发经验', '擅长PPT制作', '有创业热情'], deadline: '报名截止：3天后', avatar: '💡' },
  { id: 2, type: 'study', typeLabel: '学习小组', title: '英语口语练习小组', status: 'ongoing', statusLabel: '进行中', current: 6, max: 8, description: '每周两次线下英语角，提升口语表达能力。', requirements: ['有一定英语基础', '愿意开口练习'], deadline: '长期进行', avatar: '🗣️' },
  { id: 3, type: 'sports', typeLabel: '运动搭子', title: '羽毛球周末约球', status: 'recruiting', statusLabel: '招募中', current: 3, max: 4, description: '每周日下午体育馆羽毛球，找喜欢运动的搭子。', requirements: ['热爱运动', '有羽毛球基础'], deadline: '长期招募', avatar: '🏸' },
  { id: 4, type: 'project', typeLabel: '项目合作', title: '毕业论文互助小组', status: 'full', statusLabel: '已满员', current: 5, max: 5, description: '每周讨论论文进度，互相修改提建议。', requirements: ['正在写论文', '愿意分享'], deadline: '学期结束', avatar: '📝' }
])

const filteredTeams = computed(() => {
  return teams.value.filter(t => {
    if (teamFilter.value.type && t.type !== teamFilter.value.type) return false
    if (teamFilter.value.status && t.status !== teamFilter.value.status) return false
    return true
  })
})

const joinTeam = (team) => {
  if (team.status === 'full') return
  alert('已发送申请，请等待队长审核！')
}

// 新闻播报（真实数据，点击查看原文）
const newsItems = ref([
  { id: 1, category: 'academic', categoryLabel: '学术动态', icon: '🎓', title: '山东大学巴基斯坦研究中心揭牌仪式举行', summary: '巴基斯坦驻华大使、山东大学校长等出席揭牌仪式，标志着中巴学术合作迈上新台阶。', source: '山大视点', time: '2026-06-20', views: 2156, link: 'https://www.view.sdu.edu.cn/info/1003/209162.htm' },
  { id: 2, category: 'academic', categoryLabel: '学术动态', icon: '📜', title: '中国国际共产主义运动史学会2025年年会在山东大学举办', summary: '年会以"中华民族伟大复兴与当代世界社会主义"为主题，来自全国高校的百余位学者参会研讨。', source: '政管学院', time: '2026-06-18', views: 1890, link: 'https://pspa.sdu.edu.cn/info/1081/17780.htm' },
  { id: 3, category: 'academic', categoryLabel: '学术动态', icon: '🌏', title: '上合组织国家科教与经贸融合论坛在山东大学举办', summary: '来自上合组织成员国的专家学者齐聚山大，共商科教合作与经贸融合新路径。', source: '山大视点', time: '2026-06-15', views: 1678, link: 'https://www.view.sdu.edu.cn/info/1003/205454.htm' },
  { id: 4, category: 'notice', categoryLabel: '通知公告', icon: '📢', title: '政管学院博士后招聘启事（随时受理申请）', summary: '政治学与公共管理学院面向海内外公开招聘博士后研究人员，待遇优厚，随时受理申请。', source: '政管学院', time: '2026-06-10', views: 3456, link: 'https://pspa.sdu.edu.cn/info/1201/17536.htm' },
  { id: 5, category: 'notice', categoryLabel: '通知公告', icon: '📋', title: '2026年剑南春强国青年奖学金拟推荐人选公示', summary: '经学院评审，现将2026年剑南春强国青年奖学金拟推荐人选予以公示，接受师生监督。', source: '政管学院', time: '2026-06-16', views: 2890, link: 'https://pspa.sdu.edu.cn/info/1049/18808.htm' },
  { id: 6, category: 'award', categoryLabel: '科研动态', icon: '🏆', title: '边琦：知识·行为·制度——我国地方政府危机学习模式与进阶路径', summary: '政管学院边琦老师在权威期刊发表论文，深入剖析我国地方政府危机学习的内在机制与演进路径。', source: '政管学院', time: '2026-06-12', views: 1234, link: 'https://pspa.sdu.edu.cn/info/1030/18804.htm' },
  { id: 7, category: 'award', categoryLabel: '科研动态', icon: '📄', title: '李慧明 宋建新：欧盟竞争力战略中的工业脱碳行动', summary: '论文系统分析了欧盟工业脱碳的战略考量、实施路径及其对华影响，具有重要政策参考价值。', source: '政管学院', time: '2026-05-26', views: 987, link: 'https://pspa.sdu.edu.cn/info/1030/18739.htm' },
  { id: 8, category: 'activity', categoryLabel: '校园生活', icon: '🎉', title: '政管学院在2025级本科生军训工作中斩获佳绩', summary: '政管学院2025级本科生在军训中表现突出，荣获多项表彰，展现了良好的精神风貌。', source: '政管学院', time: '2025-09-22', views: 1567, link: 'https://pspa.sdu.edu.cn/info/1048/17683.htm' }
])
</script>

<style scoped>
.tree-hole {
  padding: 20px;
  background: linear-gradient(135deg, #0a1628 0%, #0d2040 50%, #050d1f 100%);
  min-height: 100vh;
}

.page-header {
  text-align: center;
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 36px;
  color: #fff;
  background: linear-gradient(135deg, #00d4ff 0%, #7b2cbf 50%, #faad14 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0 0 8px;
}

.page-header p {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
}

.tab-nav {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: rgba(10, 25, 50, 0.6);
  border-radius: 16px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  margin-bottom: 24px;
  overflow-x: auto;
}

.tab-btn {
  flex: 1;
  min-width: 120px;
  padding: 12px 20px;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
}

.tab-btn:hover {
  background: rgba(0, 212, 255, 0.2);
  border-color: rgba(0, 212, 255, 0.4);
  color: #fff;
}

.tab-btn.active {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.3), rgba(123, 44, 191, 0.3));
  border-color: rgba(0, 212, 255, 0.6);
  color: #00d4ff;
  box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3);
}

.tab-icon {
  font-size: 18px;
}

.content-area {
  min-height: 500px;
}

/* 心情分享样式 */
.post-card {
  background: rgba(10, 25, 50, 0.8);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
}

.create-post {
  border-color: rgba(0, 212, 255, 0.4);
  background: rgba(0, 212, 255, 0.1);
}

.post-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.avatar-mask {
  width: 40px;
  height: 40px;
  background: rgba(0, 212, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.anonymous-tag {
  font-size: 12px;
  color: rgba(0, 212, 255, 0.8);
  background: rgba(0, 212, 255, 0.1);
  padding: 4px 12px;
  border-radius: 8px;
}

.post-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.mood-badge {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 8px;
}

.mood-badge.positive {
  background: rgba(82, 196, 26, 0.2);
  color: #52c41a;
}

.mood-badge.negative {
  background: rgba(250, 173, 20, 0.2);
  color: #faad14;
}

.mood-badge.neutral {
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
}

.post-input {
  width: 100%;
  min-height: 80px;
  background: rgba(0, 20, 40, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  color: #fff;
  font-size: 14px;
  padding: 12px;
  resize: vertical;
  outline: none;
}

.post-input:focus {
  border-color: rgba(0, 212, 255, 0.5);
}

.mood-tags {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.mood-tag {
  padding: 6px 14px;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mood-tag.selected {
  background: rgba(0, 212, 255, 0.3);
  border-color: rgba(0, 212, 255, 0.5);
  color: #00d4ff;
}

.publish-btn {
  margin-top: 16px;
  padding: 10px 24px;
  background: linear-gradient(135deg, #00d4ff, #7b2cbf);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.publish-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 20px rgba(0, 212, 255, 0.4);
}

.post-content {
  font-size: 15px;
  color: #fff;
  line-height: 1.6;
  margin-bottom: 12px;
}

.post-actions {
  display: flex;
  gap: 16px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: rgba(0, 212, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
}

.comments-section {
  margin-top: 16px;
  padding: 12px;
  background: rgba(0, 20, 40, 0.4);
  border-radius: 12px;
}

.comment-item {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}

.comment-avatar {
  font-size: 18px;
}

.comment-text {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
}

.comment-input {
  width: 100%;
  padding: 8px 12px;
  background: rgba(10, 25, 50, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  color: #fff;
  font-size: 13px;
  outline: none;
}

/* 吐槽好评样式 */
.review-categories {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.cat-btn {
  padding: 10px 20px;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.cat-btn.active {
  background: rgba(0, 212, 255, 0.3);
  border-color: rgba(0, 212, 255, 0.5);
  color: #00d4ff;
}

.review-card {
  background: rgba(10, 25, 50, 0.8);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
}

.review-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.review-avatar {
  font-size: 24px;
}

.review-target {
  font-size: 16px;
  color: #fff;
  font-weight: 600;
}

.rating-stars {
  display: flex;
  gap: 4px;
}

.star {
  font-size: 16px;
  opacity: 0.3;
}

.star.filled {
  opacity: 1;
}

.review-content {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.6;
  margin-bottom: 12px;
}

.review-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.review-tag {
  font-size: 12px;
  padding: 4px 10px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 6px;
  color: rgba(0, 212, 255, 0.8);
}

.review-footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

/* 暖心鼓励样式 */
.warm-wall {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.warm-card {
  background: rgba(10, 25, 50, 0.8);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 16px;
  padding: 20px;
}

.warm-card.quote {
  border-color: rgba(0, 212, 255, 0.3);
  background: rgba(0, 212, 255, 0.1);
}

.warm-card.encourage {
  border-color: rgba(123, 44, 191, 0.3);
  background: rgba(123, 44, 191, 0.1);
}

.warm-card.story {
  border-color: rgba(250, 173, 20, 0.3);
  background: rgba(250, 173, 20, 0.1);
}

.warm-content {
  margin-bottom: 12px;
}

.warm-quote {
  display: block;
  font-size: 15px;
  color: #fff;
  line-height: 1.6;
  margin-bottom: 8px;
}

.warm-author {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

.warm-stats {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.add-warm {
  background: rgba(10, 25, 50, 0.8);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 16px;
  padding: 20px;
}

.warm-input {
  width: 100%;
  min-height: 60px;
  background: rgba(0, 20, 40, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  color: #fff;
  font-size: 14px;
  padding: 12px;
  resize: vertical;
  outline: none;
  margin-bottom: 12px;
}

.warm-btn {
  padding: 10px 24px;
  background: linear-gradient(135deg, #faad14, #52c41a);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}

/* 课程评价样式 */
.course-search {
  margin-bottom: 20px;
}

.search-input {
  width: 100%;
  padding: 12px 16px;
  background: rgba(0, 20, 40, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  color: #fff;
  font-size: 14px;
  outline: none;
}

.search-input:focus {
  border-color: rgba(0, 212, 255, 0.5);
}

.course-card {
  background: rgba(10, 25, 50, 0.8);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
}

.course-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.course-name {
  font-size: 16px;
  color: #fff;
  margin: 0 0 4px;
}

.course-teacher {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

.course-rating {
  text-align: right;
}

.avg-rating {
  font-size: 24px;
  color: #faad14;
  font-weight: bold;
}

.rating-bar {
  width: 80px;
  height: 6px;
  background: rgba(250, 173, 20, 0.2);
  border-radius: 3px;
  margin-top: 4px;
}

.rating-fill {
  height: 100%;
  background: linear-gradient(90deg, #faad14, #52c41a);
  border-radius: 3px;
}

.course-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.course-tag {
  font-size: 12px;
  padding: 4px 10px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 6px;
  color: rgba(0, 212, 255, 0.8);
}

.course-stats {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

/* 课程互助样式 */
.help-types {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.type-btn {
  padding: 10px 20px;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.type-btn.active {
  background: rgba(0, 212, 255, 0.3);
  border-color: rgba(0, 212, 255, 0.5);
  color: #00d4ff;
}

.help-card {
  background: rgba(10, 25, 50, 0.8);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
}

.help-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.help-avatar {
  font-size: 24px;
}

.help-type-tag {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
}

.help-course {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}

.help-content {
  font-size: 14px;
  color: #fff;
  line-height: 1.6;
  margin-bottom: 12px;
}

.help-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.help-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.help-action {
  padding: 8px 16px;
  background: linear-gradient(135deg, #00d4ff, #7b2cbf);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
}

/* 比赛组队样式 */
.team-filters {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.filter-select {
  padding: 10px 16px;
  background: rgba(0, 20, 40, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  color: #fff;
  font-size: 14px;
  outline: none;
}

.team-card {
  background: rgba(10, 25, 50, 0.8);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
}

.team-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.team-avatar {
  font-size: 28px;
}

.team-title {
  font-size: 16px;
  color: #fff;
  font-weight: 600;
}

.team-status {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
}

.team-status.recruiting {
  background: rgba(82, 196, 26, 0.2);
  color: #52c41a;
}

.team-status.full {
  background: rgba(250, 173, 20, 0.2);
  color: #faad14;
}

.team-status.ongoing {
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
}

.team-info {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.team-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.5;
  margin-bottom: 12px;
}

.team-requirements {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.req-tag {
  font-size: 12px;
  padding: 4px 10px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 6px;
  color: rgba(0, 212, 255, 0.8);
}

.team-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.team-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.team-join {
  padding: 8px 16px;
  background: linear-gradient(135deg, #00d4ff, #7b2cbf);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
}

.team-join:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 新闻播报样式 */
.news-list {
  display: grid;
  gap: 16px;
}

.news-card {
  background: rgba(10, 25, 50, 0.8);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 16px;
  padding: 20px;
  display: flex;
  gap: 20px;
  text-decoration: none;
  color: inherit;
  cursor: pointer;
  transition: all 0.3s ease;
}

.news-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 30px rgba(0, 212, 255, 0.15);
}

.news-card.academic {
  border-color: rgba(0, 212, 255, 0.3);
}

.news-card.activity {
  border-color: rgba(123, 44, 191, 0.3);
}

.news-card.notice {
  border-color: rgba(250, 173, 20, 0.3);
}

.news-card.award {
  border-color: rgba(82, 196, 26, 0.3);
}

/* 发布卡片通用样式 */
.publish-card {
  background: rgba(0, 212, 255, 0.08);
  border: 1px dashed rgba(0, 212, 255, 0.4);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
}
.publish-title {
  font-size: 15px;
  color: #00d4ff;
  font-weight: 600;
  margin-bottom: 14px;
}
.publish-row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  align-items: center;
}
.publish-select {
  background: rgba(0, 20, 40, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 10px;
  color: #fff;
  padding: 10px 14px;
  font-size: 14px;
  outline: none;
  min-width: 120px;
}
.publish-select option { background: #0a1628; color: #fff; }
.publish-input {
  background: rgba(0, 20, 40, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 10px;
  color: #fff;
  padding: 10px 14px;
  font-size: 14px;
  outline: none;
}
.publish-input:focus, .publish-select:focus, .publish-textarea:focus {
  border-color: rgba(0, 212, 255, 0.5);
}
.publish-textarea {
  width: 100%;
  min-height: 60px;
  background: rgba(0, 20, 40, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 10px;
  color: #fff;
  padding: 10px 14px;
  font-size: 14px;
  resize: vertical;
  outline: none;
  margin-bottom: 12px;
  box-sizing: border-box;
}
.rating-picker {
  display: flex;
  gap: 4px;
}
.star-picker {
  font-size: 24px;
  cursor: pointer;
  filter: grayscale(1) opacity(0.4);
  transition: all 0.3s;
}
.star-picker.active {
  filter: none;
  transform: scale(1.1);
}
.publish-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.tag-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  flex: 1;
}
.pick-tag {
  padding: 5px 12px;
  border-radius: 14px;
  background: rgba(0, 212, 255, 0.08);
  border: 1px solid rgba(0, 212, 255, 0.2);
  color: rgba(255,255,255,0.6);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
}
.pick-tag:hover {
  border-color: rgba(0, 212, 255, 0.5);
  color: #fff;
}
.pick-tag.selected {
  background: rgba(0, 212, 255, 0.2);
  border-color: #00d4ff;
  color: #00d4ff;
}
.publish-submit {
  padding: 10px 24px;
  background: linear-gradient(135deg, #00d4ff, #7b2cbf);
  border: none;
  border-radius: 10px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.3s;
}
.publish-submit:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 212, 255, 0.4);
}

.news-image {
  width: 80px;
  height: 80px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
}

.news-content {
  flex: 1;
}

.news-category-tag {
  font-size: 12px;
  padding: 4px 10px;
  background: rgba(0, 212, 255, 0.2);
  border-radius: 6px;
  color: #00d4ff;
  margin-bottom: 8px;
  display: inline-block;
}

.news-title {
  font-size: 16px;
  color: #fff;
  margin: 8px 0;
}

.news-summary {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
  margin-bottom: 12px;
}

.news-footer {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}
</style>