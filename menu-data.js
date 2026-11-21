/* =========================================================
   小家菜单 · 数据源
   ---------------------------------------------------------
   想改菜单，只改这个文件：
   - MENU_SETTINGS：标题、副标题、开场封面文案、分类（tab）
   - MENU_ITEMS：每道菜
       name        菜名
       en          英文名（没有就留空）
       img         配图路径（如 images/xxx.webp，可留空）
       cat         所属分类 key（对应 MENU_SETTINGS.categories[].key）
       flavor      口味标签（显示在卡片右侧）
       time        耗时
       level       难度：新手 / 顺手 / 慢炖
       serve       份量
       intro       一句话介绍（详情页顶部）
       ingredients 食材数组
       steps       做法步骤数组
       tips        小贴士（可留空）
       tag         角标（可留空，如：招牌 / 快手 / 下饭）
       hidden      true 则不显示
   ========================================================= */

window.MENU_SETTINGS = {
  brand: "小家",
  title: "小家菜单",
  subtitle: "一屋两人 · 三餐四季 · 朋友来了先点菜",
  eyebrow: "HOME KITCHEN · 预点菜",
  coverSub: "来做客，先点菜",
  enterLabel: "开始点菜 →",

  tabs: [
    { key: "all", label: "全部", en: "All" },
    { key: "home", label: "家常", en: "Home" },
    { key: "soup", label: "汤羹", en: "Soup" },
    { key: "staple", label: "主食", en: "Staple" },
    { key: "sweet", label: "甜品", en: "Sweet" },
    { key: "drink", label: "饮品", en: "Drink" }
  ],

  // 分类顺序 = 「全部」视图里的分组顺序
  categories: [
    { key: "home",   label: "家常小炒", en: "Home",   note: "灶台边的日常", icon: "katsu" },
    { key: "soup",   label: "汤羹",    en: "Soup",   note: "小火慢煨", icon: "penguin" },
    { key: "staple", label: "主食",    en: "Staple", note: "一碗管饱", icon: "bear" },
    { key: "sweet",  label: "甜品",    en: "Sweet",  note: "饭后一点甜", icon: "tapioca" },
    { key: "drink",  label: "饮品",    en: "Drink",  note: "冰的、热的", icon: "lizard" }
  ]
};

window.MENU_ITEMS = [
  /* ---------------- 家常小炒 ---------------- */
  {
    name: "番茄炒蛋",
    en: "Tomato & Egg",
    img: "images/tomato-egg.webp",
    cat: "home",
    flavor: "酸甜 · 下饭",
    time: "10 分钟",
    level: "新手",
    serve: "2 人份",
    tag: "招牌",
    intro: "鸡蛋要嫩，番茄要出沙，汤汁拿来拌饭最好。",
    ingredients: ["番茄 2 个", "鸡蛋 3 个", "小葱 1 根", "白糖 1 小勺", "盐 适量", "食用油 2 勺"],
    steps: [
      "番茄顶部划十字，开水烫 30 秒去皮，切滚刀块；鸡蛋加一小撮盐打散。",
      "热锅凉油，倒入蛋液，边缘凝固就推散，七成熟盛出。",
      "补一点油，下番茄中火炒到出汁变软，加糖和盐调味。",
      "倒回鸡蛋翻匀，撒葱花出锅。"
    ],
    tips: "糖不是为了甜，是为了压住番茄的酸。鸡蛋别炒老，回锅后翻两下就关火。"
  },
  {
    name: "青椒肉丝",
    en: "Pork with Green Pepper",
    img: "images/pepper-pork.webp",
    cat: "home",
    flavor: "咸鲜 · 微辣",
    time: "15 分钟",
    level: "新手",
    serve: "2 人份",
    tag: "下饭",
    intro: "肉丝滑、青椒脆，一盘能下两碗饭。",
    ingredients: ["猪里脊 200g", "青椒 3 个", "蒜 3 瓣", "生抽 1 勺", "淀粉 1 小勺", "料酒 1 勺", "盐 适量"],
    steps: [
      "里脊切细丝，加料酒、生抽、淀粉抓匀，淋一勺油封住，腌 10 分钟。",
      "青椒去籽切丝，蒜切片。",
      "热锅滑油，肉丝下锅快速划散至变色，盛出。",
      "底油爆香蒜片，下青椒大火炒 30 秒，倒回肉丝，加盐翻匀出锅。"
    ],
    tips: "肉丝腌的时候加点油，下锅不粘不柴。全程大火，青椒才脆。"
  },
  {
    name: "麻婆豆腐",
    en: "Mapo Tofu",
    img: "images/mapo-tofu.webp",
    cat: "home",
    flavor: "麻辣 · 烫口",
    time: "20 分钟",
    level: "顺手",
    serve: "2 人份",
    tag: "招牌",
    intro: "麻、辣、烫、香、酥、嫩，六样占全了才算合格。",
    ingredients: ["嫩豆腐 1 盒", "牛肉末 80g", "郫县豆瓣酱 1 勺", "豆豉 1 小勺", "花椒粉 适量", "蒜末 适量", "淀粉水 半碗", "小葱 1 根"],
    steps: [
      "豆腐切 2cm 方块，淡盐水浸泡 5 分钟去豆腥，捞出沥干。",
      "热油炒牛肉末至酥香，加豆瓣酱、豆豉、蒜末炒出红油。",
      "加一碗热水烧开，轻轻推入豆腐，中小火煮 4 分钟。",
      "分两次淋淀粉水勾芡，出锅撒花椒粉和葱花。"
    ],
    tips: "豆腐别用铲子翻，端着锅轻推。花椒粉最后撒，香气才不散。"
  },
  {
    name: "可乐鸡翅",
    en: "Cola Chicken Wings",
    img: "images/cola-wings.webp",
    cat: "home",
    flavor: "甜咸 · 焦香",
    time: "30 分钟",
    level: "新手",
    serve: "2 人份",
    intro: "有手就会，收汁到发亮就对了。",
    ingredients: ["鸡中翅 10 个", "可乐 1 罐", "姜 3 片", "生抽 2 勺", "老抽 半勺", "料酒 1 勺"],
    steps: [
      "鸡翅两面各划两刀，冷水下锅焯水，捞出擦干。",
      "少油将鸡翅煎至两面金黄。",
      "加姜片、料酒、生抽、老抽，倒入可乐至没过鸡翅。",
      "大火烧开转中小火 15 分钟，最后大火收汁到浓稠挂壁。"
    ],
    tips: "可乐本身够甜，不用再加糖。收汁时勤翻动，别糊底。"
  },
  {
    name: "蒜蓉西兰花",
    en: "Broccoli with Garlic",
    img: "images/garlic-broccoli.webp",
    cat: "home",
    flavor: "清爽 · 蒜香",
    time: "10 分钟",
    level: "新手",
    serve: "2 人份",
    intro: "颜色翠绿、口感脆嫩，配什么主食都行。",
    ingredients: ["西兰花 1 颗", "蒜 5 瓣", "盐 适量", "蚝油 1 勺", "食用油 1 勺"],
    steps: [
      "西兰花切小朵，淡盐水泡 10 分钟洗净。",
      "水开加几滴油和一点盐，下西兰花焯 60 秒，捞出过凉水。",
      "热油爆香蒜末，下西兰花大火翻炒。",
      "加盐和蚝油，翻匀即可出锅。"
    ],
    tips: "焯水时加油和盐，颜色才绿；过凉水能保住脆感。"
  },
  {
    name: "红烧排骨",
    en: "Braised Pork Ribs",
    img: "images/braised-ribs.webp",
    cat: "home",
    flavor: "浓油 · 赤酱",
    time: "60 分钟",
    level: "慢炖",
    serve: "3 人份",
    tag: "周末",
    intro: "炖够时间，筷子一夹就脱骨。",
    ingredients: ["猪肋排 500g", "冰糖 15g", "生抽 2 勺", "老抽 半勺", "料酒 2 勺", "姜 4 片", "八角 1 颗", "桂皮 1 小段"],
    steps: [
      "排骨冷水下锅，加姜片料酒焯水，撇净浮沫捞出。",
      "锅里少油下冰糖，小火炒到琥珀色，下排骨翻炒上色。",
      "加生抽、老抽、姜、八角、桂皮，倒热水没过排骨。",
      "大火烧开转小火炖 40 分钟，最后大火收汁。"
    ],
    tips: "炒糖色别走神，一变琥珀色立刻下排骨，深了会发苦。"
  },
  {
    name: "醋溜土豆丝",
    en: "Vinegar Potato Shreds",
    img: "images/vinegar-potato.webp",
    cat: "home",
    flavor: "酸辣 · 爽脆",
    time: "12 分钟",
    level: "新手",
    serve: "2 人份",
    intro: "切得越细越脆，锅气越足越香。",
    ingredients: ["土豆 2 个", "干辣椒 3 个", "蒜 2 瓣", "白醋 2 勺", "盐 适量", "花椒 10 粒"],
    steps: [
      "土豆切细丝，清水反复冲洗掉淀粉，泡 5 分钟沥干。",
      "热油下花椒炸香捞出，下干辣椒和蒜末。",
      "倒入土豆丝大火快炒 1 分钟。",
      "沿锅边淋白醋，加盐炒匀出锅。"
    ],
    tips: "醋分两次放：一次沿锅边激香，一次出锅前补酸。"
  },
  {
    name: "冬瓜虾皮汤",
    en: "Winter Melon Soup",
    img: "images/winter-melon-soup.webp",
    cat: "home",
    flavor: "清淡 · 鲜",
    time: "15 分钟",
    level: "新手",
    serve: "2 人份",
    intro: "夏天最省事的一碗汤。",
    ingredients: ["冬瓜 300g", "虾皮 1 小把", "姜 2 片", "盐 适量", "香油 几滴", "小葱 1 根"],
    steps: [
      "冬瓜去皮切薄片，虾皮温水泡洗一下。",
      "锅里少油，下姜片和虾皮炒香。",
      "加水烧开，下冬瓜煮 6 分钟至透明。",
      "加盐调味，滴香油、撒葱花。"
    ],
    tips: "虾皮先炒过，汤才鲜；冬瓜煮到透明就关火，别煮烂。"
  },

  /* ---------------- 汤羹 ---------------- */
  {
    name: "番茄牛腩汤",
    en: "Tomato Beef Soup",
    img: "images/tomato-beef-soup.webp",
    cat: "soup",
    flavor: "浓郁 · 微酸",
    time: "90 分钟",
    level: "慢炖",
    serve: "4 人份",
    tag: "招牌",
    intro: "番茄熬到化开，牛腩炖到入口即化。",
    ingredients: ["牛腩 500g", "番茄 4 个", "洋葱 半个", "姜 4 片", "番茄膏 2 勺", "盐 适量", "白胡椒 适量"],
    steps: [
      "牛腩切块冷水下锅焯水，撇沫捞出。",
      "番茄去皮切块，洋葱切丁。",
      "少油炒洋葱至透明，加番茄炒出沙，加番茄膏炒匀。",
      "倒入牛腩和热水，小火炖 60 分钟以上。",
      "加盐和白胡椒调味。"
    ],
    tips: "水一次加够，中途加冷水肉会紧。"
  },
  {
    name: "冬瓜排骨汤",
    en: "Winter Melon & Rib Soup",
    img: "images/melon-rib-soup.webp",
    cat: "soup",
    flavor: "清甜 · 解腻",
    time: "60 分钟",
    level: "慢炖",
    serve: "3 人份",
    intro: "排骨先炖，冬瓜后下，汤清不浑。",
    ingredients: ["猪小排 400g", "冬瓜 400g", "姜 3 片", "枸杞 1 小把", "盐 适量", "料酒 1 勺"],
    steps: [
      "排骨冷水下锅焯水洗净。",
      "加姜片、料酒和足量热水，小火炖 40 分钟。",
      "冬瓜去皮切厚片下锅，再煮 15 分钟。",
      "加盐，撒枸杞，关火。"
    ],
    tips: "冬瓜后放，才不会炖化成一锅水。"
  },
  {
    name: "紫菜蛋花汤",
    en: "Seaweed Egg Drop Soup",
    img: "images/seaweed-egg-soup.webp",
    cat: "soup",
    flavor: "鲜 · 暖",
    time: "8 分钟",
    level: "新手",
    serve: "2 人份",
    tag: "上菜快",
    intro: "五分钟能上桌的救命汤。",
    ingredients: ["紫菜 1 小把", "鸡蛋 1 个", "虾皮 1 小勺", "香油 几滴", "盐 适量", "白胡椒 适量", "小葱 1 根"],
    steps: [
      "水烧开，下紫菜和虾皮。",
      "鸡蛋打散，关小火，画圈淋入蛋液，静置 10 秒再搅。",
      "加盐、白胡椒，滴香油，撒葱花。"
    ],
    tips: "蛋液要在水微沸时淋，火太大蛋花会老。"
  },
  {
    name: "酸辣汤",
    en: "Hot & Sour Soup",
    img: "images/hot-sour-soup.webp",
    cat: "soup",
    flavor: "酸辣 · 开胃",
    time: "20 分钟",
    level: "顺手",
    serve: "3 人份",
    intro: "白胡椒和醋的比例是灵魂。",
    ingredients: ["豆腐 半盒", "木耳 5 朵", "胡萝卜 半根", "鸡蛋 1 个", "香醋 2 勺", "白胡椒 1 小勺", "淀粉水 半碗", "生抽 1 勺"],
    steps: [
      "木耳泡发切丝，豆腐、胡萝卜切细丝。",
      "水开下所有丝，煮 4 分钟。",
      "加生抽、盐，淋淀粉水勾薄芡。",
      "淋蛋液成蛋花，关火后加香醋和白胡椒。"
    ],
    tips: "醋一定关火后放，煮过就不酸了。"
  },
  {
    name: "玉米胡萝卜排骨汤",
    en: "Corn & Carrot Soup",
    img: "images/corn-carrot-soup.webp",
    cat: "soup",
    flavor: "清甜 · 润",
    time: "70 分钟",
    level: "慢炖",
    serve: "4 人份",
    intro: "不用放糖，玉米自己就甜。",
    ingredients: ["排骨 400g", "甜玉米 1 根", "胡萝卜 1 根", "姜 3 片", "盐 适量"],
    steps: [
      "排骨焯水洗净，玉米切段，胡萝卜切滚刀块。",
      "全部下锅，加姜片和足量热水。",
      "大火烧开转小火炖 50 分钟。",
      "出锅前加盐。"
    ],
    tips: "玉米芯一起炖更甜，出锅前捞出即可。"
  },

  /* ---------------- 主食 ---------------- */
  {
    name: "葱油拌面",
    en: "Scallion Oil Noodles",
    img: "images/scallion-noodles.webp",
    cat: "staple",
    flavor: "酱香 · 葱油",
    time: "15 分钟",
    level: "新手",
    serve: "1 人份",
    tag: "上菜快",
    intro: "葱油熬得好，一碗面就够了。",
    ingredients: ["细面 150g", "小葱 1 把", "生抽 2 勺", "老抽 半勺", "白糖 1 小勺", "食用油 4 勺"],
    steps: [
      "小葱切段，冷油下锅，小火慢熬到葱变焦黄，捞出葱段。",
      "葱油里加生抽、老抽、糖，小火煮开关火。",
      "面条煮熟捞出，趁热拌入葱油酱汁。",
      "撒上炸好的葱段。"
    ],
    tips: "熬葱油一定小火，葱黑了油就苦。"
  },
  {
    name: "扬州炒饭",
    en: "Yangzhou Fried Rice",
    img: "images/fried-rice.webp",
    cat: "staple",
    flavor: "咸鲜 · 粒粒分明",
    time: "20 分钟",
    level: "顺手",
    serve: "2 人份",
    tag: "招牌",
    intro: "剩饭的最佳归宿，配菜比饭还多。",
    ingredients: ["隔夜米饭 2 碗", "鸡蛋 2 个", "虾仁 80g", "火腿丁 50g", "青豆 50g", "胡萝卜丁 50g", "盐 适量", "白胡椒 适量"],
    steps: [
      "虾仁焯熟，鸡蛋炒散盛出。",
      "热油下胡萝卜丁、青豆炒 1 分钟。",
      "倒入米饭，用铲子压散，大火翻炒到粒粒松散。",
      "加虾仁、火腿、鸡蛋，盐和白胡椒调味，翻匀出锅。"
    ],
    tips: "米饭提前用手抓散，下锅不结块。"
  },
  {
    name: "猪肉白菜饺子",
    en: "Pork & Cabbage Dumplings",
    img: "images/dumplings.webp",
    cat: "staple",
    flavor: "鲜香 · 多汁",
    time: "90 分钟",
    level: "慢炖",
    serve: "4 人份",
    tag: "周末",
    intro: "一次包一批冻起来，随时能煮。",
    ingredients: ["猪肉馅 400g", "白菜 半颗", "饺子皮 500g", "姜末 适量", "生抽 2 勺", "香油 2 勺", "盐 适量"],
    steps: [
      "白菜切碎加盐杀水 15 分钟，攥干。",
      "肉馅加姜末、生抽、盐，顺一个方向搅上劲。",
      "拌入白菜和香油，馅料拌匀。",
      "包好后水开下锅，点三次凉水，浮起即熟。"
    ],
    tips: "白菜一定要攥干，不然馅会出水破皮。"
  },
  {
    name: "鸡蛋羹",
    en: "Steamed Egg Custard",
    img: "images/egg-custard.webp",
    cat: "staple",
    flavor: "滑嫩 · 清淡",
    time: "15 分钟",
    level: "新手",
    serve: "1 人份",
    intro: "水和蛋的比例是 1.5 : 1。",
    ingredients: ["鸡蛋 2 个", "温水 150ml", "盐 少许", "生抽 半勺", "香油 几滴", "小葱 适量"],
    steps: [
      "鸡蛋打散，加温水和盐搅匀。",
      "过筛两遍去掉气泡，倒入碗中，盖保鲜膜扎几个孔。",
      "水开上锅，中小火蒸 10 分钟，关火焖 2 分钟。",
      "淋生抽、香油，撒葱花。"
    ],
    tips: "必须用温水，冷水蒸出来会有蜂窝。"
  },

  /* ---------------- 甜品 ---------------- */
  {
    name: "银耳莲子羹",
    en: "Snow Fungus Soup",
    img: "images/snow-fungus.webp",
    cat: "sweet",
    flavor: "清甜 · 糯",
    time: "60 分钟",
    level: "慢炖",
    serve: "3 人份",
    intro: "炖到出胶，凉了更好喝。",
    ingredients: ["银耳 1 朵", "莲子 20 颗", "红枣 6 颗", "枸杞 1 小把", "冰糖 适量"],
    steps: [
      "银耳提前泡发 1 小时，去黄蒂撕小朵。",
      "银耳、莲子、红枣加水，大火烧开转小火炖 40 分钟。",
      "加冰糖再炖 10 分钟至出胶。",
      "关火前放枸杞。"
    ],
    tips: "银耳撕得越碎越容易出胶。"
  },
  {
    name: "酒酿圆子",
    en: "Fermented Rice Balls",
    img: "images/rice-balls.webp",
    cat: "sweet",
    flavor: "甜 · 微醺",
    time: "15 分钟",
    level: "新手",
    serve: "2 人份",
    intro: "冬天睡前来一碗，从胃暖到脚。",
    ingredients: ["酒酿 200g", "小圆子 100g", "鸡蛋 1 个", "枸杞 少许", "冰糖 适量", "淀粉水 少许"],
    steps: [
      "水开下小圆子，浮起后加酒酿。",
      "加冰糖煮化，淋少许淀粉水增稠。",
      "蛋液画圈淋入，关火。",
      "撒枸杞。"
    ],
    tips: "酒酿别久煮，酒香会跑。"
  },
  {
    name: "红豆沙",
    en: "Red Bean Paste",
    img: "images/red-bean.webp",
    cat: "sweet",
    flavor: "绵密 · 甜",
    time: "80 分钟",
    level: "慢炖",
    serve: "4 人份",
    intro: "煮到一压就散，再炒到能抱团。",
    ingredients: ["红豆 250g", "冰糖 80g", "食用油 2 勺", "陈皮 1 小片"],
    steps: [
      "红豆提前泡 4 小时。",
      "加水没过红豆，放陈皮，小火煮 50 分钟至软烂。",
      "用勺子压碎，加冰糖。",
      "小火翻炒到水分收干、能抱团。"
    ],
    tips: "炒的时候加油，口感才润不发干。"
  },
  {
    name: "烤红薯",
    en: "Roasted Sweet Potato",
    img: "images/roast-sweet-potato.webp",
    cat: "sweet",
    flavor: "焦糖 · 流蜜",
    time: "60 分钟",
    level: "新手",
    serve: "1 人份",
    intro: "烤箱 200 度，等它自己流糖。",
    ingredients: ["红薯 2 个", "锡纸 1 张"],
    steps: [
      "红薯洗净擦干，用叉子扎几个孔。",
      "垫锡纸，200 度烤 50–60 分钟，中途翻面。",
      "按一下变软、表面出糖浆即可。"
    ],
    tips: "选细长的蜜薯，比大个的更容易烤透流蜜。"
  },

  /* ---------------- 饮品 ---------------- */
  {
    name: "冰镇酸梅汤",
    en: "Sour Plum Drink",
    img: "images/plum-drink.webp",
    cat: "drink",
    flavor: "酸甜 · 解腻",
    time: "40 分钟",
    level: "顺手",
    serve: "4 人份",
    tag: "夏日",
    intro: "煮好冷藏，比任何饮料都解渴。",
    ingredients: ["乌梅 30g", "山楂 20g", "陈皮 5g", "甘草 3g", "冰糖 80g", "桂花 少许", "水 2L"],
    steps: [
      "所有干料冲洗一遍，清水泡 30 分钟。",
      "连水一起煮开，转小火 30 分钟。",
      "加冰糖煮化，关火撒桂花。",
      "过滤放凉，冷藏后饮用。"
    ],
    tips: "桂花最后放，煮久了会发苦。"
  },
  {
    name: "柠檬蜂蜜水",
    en: "Lemon Honey Water",
    img: "images/lemon-honey.webp",
    cat: "drink",
    flavor: "清爽 · 微酸",
    time: "5 分钟",
    level: "新手",
    serve: "1 人份",
    intro: "早上空腹一杯，或者下午犯困时。",
    ingredients: ["柠檬 1 个", "蜂蜜 2 勺", "温水 300ml", "薄荷叶 几片"],
    steps: [
      "柠檬用盐搓洗表皮，切 2 片。",
      "温水化开蜂蜜，放入柠檬片。",
      "丢几片薄荷，泡 3 分钟。"
    ],
    tips: "别用开水，蜂蜜和维 C 都怕烫。"
  },
  {
    name: "桂花酒酿饮",
    en: "Osmanthus Rice Wine",
    img: "images/osmanthus-drink.webp",
    cat: "drink",
    flavor: "甜 · 花香",
    time: "10 分钟",
    level: "新手",
    serve: "2 人份",
    intro: "热饮冷饮都行，加气泡水更像特调。",
    ingredients: ["酒酿 150g", "桂花蜜 1 勺", "气泡水 200ml", "冰块 适量"],
    steps: [
      "杯底放酒酿和桂花蜜。",
      "加满冰块，倒入气泡水。",
      "轻轻搅一下，撒干桂花。"
    ],
    tips: "酒酿先冷藏，风味更清。"
  },
  {
    name: "热可可",
    en: "Hot Cocoa",
    img: "images/hot-cocoa.webp",
    cat: "drink",
    flavor: "浓郁 · 暖",
    time: "8 分钟",
    level: "新手",
    serve: "1 人份",
    intro: "雨天的标准配置。",
    ingredients: ["可可粉 2 勺", "牛奶 250ml", "糖 1 勺", "淡奶油 少许", "棉花糖 几颗"],
    steps: [
      "可可粉加少量热牛奶搅成糊。",
      "剩余牛奶加热到微沸，倒入搅匀。",
      "加糖调味，倒入杯中。",
      "挤淡奶油，放棉花糖。"
    ],
    tips: "先把可可粉调成糊再加奶，不容易结块。"
  }
];
