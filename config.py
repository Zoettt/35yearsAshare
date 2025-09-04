# Longbridge API 配置
LONGBRIDGE_CONFIG = {
    "app_key": "9ec592b255bf54227ee47f346b8fbc67",
    "app_secret": "ca898786bf4c5cdb41045467e8dc2ce007a8551681655af6a8f0cf3d4c98c3ad",
    "access_token": "m_eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJsb25nYnJpZGdlIiwic3ViIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNzU4OTQ0MTk0LCJpYXQiOjE3NTExNjgxOTQsImFrIjoiOWVjNTkyYjI1NWJmNTQyMjdlZTQ3ZjM0NmI4ZmJjNjciLCJhYWlkIjoyMDU2MzA5NSwiYWMiOiJsYiIsIm1pZCI6MTc0NjAyNjQsInNpZCI6ImpOOFFhSE81M3hJS2ZSUmdUcm1yMkE9PSIsImJsIjozLCJ1bCI6MCwiaWsiOiJsYl8yMDU2MzA5NSJ9.M5HRdCHqPNnLv-kqRYDZpSkoI48dN5EYUmGrd6pomBAslr-ZGU5VXuDKXoWjTkx70Q621Ae2Au2Z3AlPyPXY5h5egBm7SifIaLNlQlKgAG5wFL-Jp2whF7JFY6iAxQnCPuvFwXd1Q9QI2Z2htmIzjzS9TrubQhLxAjuNEUjmOKRqgX0RVD6WWwFfLDR4pgR98bGmcNUB5pm8pePmsZznFlZU-kv08TCSBKeZT5a6VQl_ZZtXQuS4M2kESd1xtrg4fkXslSnAhki4meiMDLVY_J21BJXmG7bgAzAX2PqtD2MfvATfGL8NJWHC2qoOsa5BXpDjhliZwqjxx-8xfVrnbfTh0xO81t7_JajJ29d_VA1ebxYwr-ZIsnhEyNDxVfxXPeC5LhAb4oVH4BjzlVGEPmFgoc1tZqx-5yvAtNLNmYrsqi_M_f-VtyyMhaqNs0ChQUeMVe6Xf6saq2yWzTmRvp1I9-QEixRtyDGkgWAXGzyb6aqeW5VKhc9zYP9pKiX7Bu5wLI8Tv1vYICgTg3uKr_K5PeCMvLs_e318AxpObMEgR9vRS9Bqplms0y1J3p8Kgbr7xrvK-u2chH8jo-GguLRv_k_OrRv8PhqGa-rbP6D9s4akfZRGFgM7yJMd2V_Q0r__yyF9b-fLiTxZ1ciUdog5sbspXFY0OAqZzuLCCLM"
}

# 纳指三倍做多/做空ETF代码
NASDAQ_SYMBOLS = {
    "三倍做多纳指": "TQQQ.US",  # Direxion Daily QQQ Bull 3X Shares
    "三倍做空纳指": "SQQQ.US"   # Direxion Daily QQQ Bear 3X Shares
}

# 富时中国三倍做多/做空ETF代码
FTSE_CHINA_SYMBOLS = {
    "三倍做多富时中国": "YINN.US",  # Direxion Daily FTSE China Bull 3X Shares
    "三倍做空富时中国": "YANG.US"   # Direxion Daily FTSE China Bear 3X Shares
}

# A股ETF配置
A_SHARE_ETFS = {
    # 宽基指数ETF
    "沪深300ETF": "510300.SH",  # 华夏沪深300ETF
    "中证500ETF": "510500.SH",  # 南方中证500ETF
    "创业板ETF": "159915.SZ",   # 易方达创业板ETF
    "科创50ETF": "588000.SH",   # 华夏科创50ETF
    "上证50ETF": "510050.SH",   # 华夏上证50ETF
    "深证100ETF": "159901.SZ",  # 易方达深证100ETF
    "中证1000ETF": "512100.SH", # 南方中证1000ETF
    
    # 行业主题ETF
    "科技ETF": "515000.SH",     # 华宝科技ETF
    "医药ETF": "512010.SH",     # 易方达医药ETF
    "消费ETF": "159928.SZ",     # 汇添富消费ETF
    "金融ETF": "510230.SH",     # 国泰金融ETF
    "地产ETF": "512200.SH",     # 南方房地产ETF
    "新能源ETF": "516160.SH",   # 华安新能源ETF
    "芯片ETF": "512760.SH",     # 国泰芯片ETF
    "军工ETF": "512660.SH",     # 国泰军工ETF
    "农业ETF": "159825.SZ",     # 银华农业ETF
    "传媒ETF": "512980.SH",     # 广发传媒ETF
    "环保ETF": "512580.SH",     # 广发环保ETF
    "银行ETF": "512800.SH",     # 华宝银行ETF
    "证券ETF": "512880.SH",     # 国泰证券ETF
    "钢铁ETF": "515210.SH",     # 国泰钢铁ETF
    "煤炭ETF": "515220.SH",     # 国泰煤炭ETF
    "有色ETF": "512400.SH",     # 南方有色金属ETF
    "化工ETF": "516020.SH",     # 华安化工ETF
    "建材ETF": "516750.SH",     # 华安建材ETF
    "汽车ETF": "516110.SH",     # 华安汽车ETF
    "家电ETF": "159996.SZ",     # 国泰家电ETF
    "食品ETF": "515710.SH",     # 华安食品ETF
    "服装ETF": "159944.SZ",     # 广发服装ETF
    "旅游ETF": "159766.SZ",     # 华夏旅游ETF
    "教育ETF": "513360.SH",     # 博时教育ETF
    "游戏ETF": "516010.SH",     # 华安游戏ETF
    "云计算ETF": "516510.SH",   # 华安云计算ETF
    "人工智能ETF": "515980.SH", # 华夏人工智能ETF
    "5G ETF": "515050.SH",      # 华夏5G ETF
    "物联网ETF": "516120.SH",   # 华安物联网ETF
    "大数据ETF": "515400.SH",   # 华夏大数据ETF
    "区块链ETF": "516950.SH",   # 华安区块链ETF
    "数字货币ETF": "516960.SH", # 华安数字货币ETF
    
    # 海外ETF
    "恒生ETF": "159920.SZ",     # 易方达恒生ETF
    "纳指ETF": "513100.SH",     # 国泰纳指ETF
    "标普500ETF": "513500.SH",  # 博时标普500ETF
    "德国30ETF": "513030.SH",   # 华安德国30ETF
    "日经225ETF": "513880.SH",  # 工银日经225ETF
    "法国CAC40ETF": "513080.SH", # 华安法国CAC40ETF
    
    # 商品ETF
    "黄金ETF": "518880.SH",     # 华安黄金ETF
    "白银ETF": "161226.SZ",     # 国投白银ETF
    "原油ETF": "161129.SZ",     # 易方达原油ETF
    
    # 债券ETF
    "国债ETF": "511010.SH",     # 华夏国债ETF
    "企业债ETF": "511220.SH",   # 华宝企业债ETF
    "城投债ETF": "511280.SH",   # 华宝城投债ETF
    
    # 杠杆ETF
    "沪深300杠杆ETF": "150201.SZ", # 鹏华沪深300杠杆ETF
    "创业板杠杆ETF": "150153.SZ",  # 富国创业板杠杆ETF
    "证券杠杆ETF": "150172.SZ",    # 申万证券杠杆ETF
    "银行杠杆ETF": "150228.SZ",    # 鹏华银行杠杆ETF
    "地产杠杆ETF": "150118.SZ",    # 国泰国证房地产杠杆ETF
    "医药杠杆ETF": "150131.SZ",    # 国泰国证医药卫生杠杆ETF
    "食品杠杆ETF": "150199.SZ",    # 国泰国证食品饮料杠杆ETF
    "有色杠杆ETF": "150197.SZ",    # 国泰国证有色金属杠杆ETF
    "煤炭杠杆ETF": "150189.SZ",    # 国泰国证煤炭杠杆ETF
    "钢铁杠杆ETF": "150287.SZ",    # 国泰国证钢铁杠杆ETF
}

# 数据获取配置
DATA_CONFIG = {
    "period": "1d",  # 日线数据
    "adjust_type": "NO_ADJUST",  # 不复权
    "fields": ["open", "high", "low", "close", "volume", "turnover"]  # 获取的字段
} 