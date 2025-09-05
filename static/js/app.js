/* 交互式股票图表Web应用JavaScript */

$(document).ready(function() {
    
    // 全局变量
    let stocksData = [];
    let indicesData = [];
    let isLoading = false;
    
    // 初始化应用
    initializeApp();
    
    /**
     * 初始化应用
     */
    function initializeApp() {
        console.log('🚀 初始化交互式股票图表应用');
        
        // 初始化组件
        initializeComponents();
        
        // 绑定事件
        bindEvents();
        
        // 加载数据
        loadInitialData();
        
        // 设置默认日期
        setDefaultDates();
    }
    
    /**
     * 初始化组件
     */
    function initializeComponents() {
        // 初始化Select2多选组件，支持优化的动态搜索
        $('#stockSelect').select2({
            placeholder: '搜索并选择股票...',
            allowClear: true,
            width: '100%',
            theme: 'bootstrap-5',
            minimumInputLength: 0, // 允许立即搜索
            ajax: {
                url: '/api/stocks/search',
                dataType: 'json',
                delay: 300, // 防抖延迟300ms
                data: function (params) {
                    return {
                        q: params.term || '', // 搜索词
                        limit: 50 // 限制结果数量
                    };
                },
                processResults: function (data) {
                    if (data.success) {
                        return {
                            results: data.data.map(function(stock) {
                                return {
                                    id: stock.symbol,
                                    text: `${stock.name} (${stock.symbol})`
                                };
                            })
                        };
                    } else {
                        return { results: [] };
                    }
                },
                cache: true // 启用缓存
            }
        });
        
        $('#indexSelect').select2({
            placeholder: '选择指数...',
            allowClear: false,
            width: '100%',
            theme: 'bootstrap-5'
        });
        
        // 隐藏图表容器，显示初始消息
        $('#plotlyChart').hide();
        $('#initialMessage').show();
    }
    
    /**
     * 绑定事件
     */
    function bindEvents() {
        // 生成图表按钮
        $('#generateChart').click(function() {
            if (!isLoading) {
                generateChart();
            }
        });
        
        // 重置表单按钮
        $('#resetForm').click(function() {
            resetForm();
        });
        
        // 表单字段变化时的实时验证
        $('#stockSelect, #indexSelect').on('change', function() {
            validateForm();
        });
        
        // 回车键快捷生成图表
        $(document).keypress(function(e) {
            if (e.which === 13 && !isLoading) { // Enter键
                generateChart();
            }
        });
    }
    
    /**
     * 加载初始数据
     */
    function loadInitialData() {
        updateStatus('正在加载股票和指数数据...', true);
        
        // 并行加载股票和指数数据
        Promise.all([
            loadStocks(),
            loadIndices()
        ]).then(() => {
            updateStatus('数据加载完成，就绪', false);
            validateForm();
        }).catch((error) => {
            console.error('数据加载失败:', error);
            updateStatus('数据加载失败', false);
            showAlert('数据加载失败，请刷新页面重试', 'danger');
        });
    }
    
    /**
     * 加载股票数据（优化版 - 只加载热门股票）
     */
    function loadStocks() {
        return $.get('/api/stocks?limit=20') // 只加载热门股票
            .done(function(response) {
                if (response.success) {
                    stocksData = response.data;
                    populateStockSelect();
                    console.log(`✅ 预加载了 ${stocksData.length} 只热门股票，支持动态搜索`);
                } else {
                    throw new Error(response.error);
                }
            });
    }
    
    /**
     * 加载指数数据
     */
    function loadIndices() {
        return $.get('/api/indices')
            .done(function(response) {
                if (response.success) {
                    indicesData = response.data;
                    populateIndexSelect();
                    console.log(`✅ 加载了 ${indicesData.length} 个指数`);
                } else {
                    throw new Error(response.error);
                }
            });
    }
    
    /**
     * 填充股票选择器（优化版 - 设置默认选项）
     */
    function populateStockSelect() {
        const $stockSelect = $('#stockSelect');
        
        // 查找茅台股票
        let maotaiStock = stocksData.find(stock => stock.symbol === 'sh600519');
        
        if (maotaiStock) {
            // 手动添加茅台选项并设为选中
            const option = new Option(
                `${maotaiStock.name} (${maotaiStock.symbol})`, 
                maotaiStock.symbol, 
                true, 
                true
            );
            $stockSelect.append(option);
        } else if (stocksData.length > 0) {
            // 如果没有茅台，选择第一只股票
            const firstStock = stocksData[0];
            const option = new Option(
                `${firstStock.name} (${firstStock.symbol})`, 
                firstStock.symbol, 
                true, 
                true
            );
            $stockSelect.append(option);
        }
        
        $stockSelect.trigger('change');
        
        // 输出调试信息
        console.log(`✅ 股票选择器已初始化，支持动态搜索和防抖`);
    }
    
    /**
     * 填充指数选择器
     */
    function populateIndexSelect() {
        const $indexSelect = $('#indexSelect');
        $indexSelect.empty();
        
        indicesData.forEach(function(indexName) {
            const selected = indexName === '上证指数';
            $indexSelect.append(new Option(indexName, indexName, selected, selected));
        });
        
        $indexSelect.trigger('change');
    }
    
    /**
     * 设置默认日期
     */
    function setDefaultDates() {
        const today = new Date();
        const oneYearAgo = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
        
        // 不设置默认日期，让用户自由选择
        // $('#startDate').val(oneYearAgo.toISOString().split('T')[0]);
        // $('#endDate').val(today.toISOString().split('T')[0]);
    }
    
    /**
     * 生成图表
     */
    function generateChart() {
        if (!validateForm()) {
            return;
        }
        
        const formData = collectFormData();
        
        updateStatus('正在生成图表...', true);
        $('#plotlyChart').hide();
        $('#initialMessage').hide();
        
        // 显示加载占位符
        showLoadingChart();
        
        $.ajax({
            url: '/api/chart',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            timeout: 30000 // 30秒超时
        }).done(function(response) {
            if (response.success) {
                displayChart(response.chart);
                updateChartInfo(response.stock_count, response.index_name);
                updateStatus(`图表生成成功 (${response.stock_count}只股票)`, false);
                showAlert('图表生成成功！鼠标悬浮可查看详细数据', 'success');
            } else {
                throw new Error(response.error);
            }
        }).fail(function(xhr, status, error) {
            console.error('图表生成失败:', error);
            let errorMsg = '图表生成失败';
            if (status === 'timeout') {
                errorMsg = '请求超时，请稍后重试';
            } else if (xhr.responseJSON && xhr.responseJSON.error) {
                errorMsg = xhr.responseJSON.error;
            }
            updateStatus(errorMsg, false);
            showAlert(errorMsg, 'danger');
            showInitialMessage();
        });
    }
    
    /**
     * 收集表单数据
     */
    function collectFormData() {
        return {
            stocks: $('#stockSelect').val() || ['sh600519'],
            index: $('#indexSelect').val() || '上证指数',
            normalize: $('#normalizeCheck').is(':checked'),
            start_date: $('#startDate').val() || null,
            end_date: $('#endDate').val() || null
        };
    }
    
    /**
     * 验证表单
     */
    function validateForm() {
        const selectedStocks = $('#stockSelect').val();
        const selectedIndex = $('#indexSelect').val();
        
        const isValid = selectedStocks && selectedStocks.length > 0 && selectedIndex;
        
        $('#generateChart').prop('disabled', !isValid);
        
        return isValid;
    }
    
    /**
     * 显示图表
     */
    function displayChart(chartJson) {
        try {
            const chartData = JSON.parse(chartJson);
            
            // 确保图表容器可见
            $('#initialMessage').hide();
            $('#plotlyChart').show();
            
            // 优化图表布局以支持触摸设备
            chartData.layout.dragmode = 'pan';   // 默认为平移模式，双指拖拽=平移
            chartData.layout.scrollZoom = true;   // 启用滚轮/双指缩放
            
            // 渲染图表
            Plotly.newPlot('plotlyChart', chartData.data, chartData.layout, {
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: ['lasso2d', 'autoScale2d'],  // 保留pan2d和zoom2d按钮
                scrollZoom: true,  // 明确启用滚轮/双指缩放
                doubleClick: 'reset',  // 双击重置缩放
                touchDelay: 150,  // 触摸延迟，帮助区分单指和双指操作
                showTips: false,  // 减少触摸时的提示干扰
                toImageButtonOptions: {
                    format: 'png',
                    filename: 'stock_chart',
                    height: 600,
                    width: 1200,
                    scale: 2
                }
            });
            
            console.log('✅ 图表渲染成功');
            
        } catch (error) {
            console.error('图表渲染失败:', error);
            showAlert('图表渲染失败', 'danger');
            showInitialMessage();
        }
    }
    
    /**
     * 显示加载图表
     */
    function showLoadingChart() {
        const loadingHtml = `
            <div class="text-center p-5">
                <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <h5 class="text-muted">正在生成交互式图表...</h5>
                <p class="text-muted small">请稍候，正在处理数据并渲染图表</p>
            </div>
        `;
        
        $('#plotlyChart').html(loadingHtml).show();
    }
    
    /**
     * 显示初始消息
     */
    function showInitialMessage() {
        $('#plotlyChart').hide();
        $('#initialMessage').show();
    }
    
    /**
     * 重置表单
     */
    function resetForm() {
        // 重置选择器
        $('#stockSelect').val(['sh600519']).trigger('change');
        $('#indexSelect').val('上证指数').trigger('change');
        
        // 重置复选框和日期
        $('#normalizeCheck').prop('checked', false);
        $('#startDate').val('');
        $('#endDate').val('');
        
        // 重置状态
        updateStatus('已重置，就绪', false);
        updateChartInfo(0, '');
        
        // 显示初始消息
        showInitialMessage();
        
        // 验证表单
        validateForm();
        
        showAlert('表单已重置', 'info');
    }
    
    /**
     * 更新状态文本
     */
    function updateStatus(message, loading) {
        isLoading = loading;
        $('#statusText').text(message);
        
        if (loading) {
            $('#loadingSpinner').removeClass('d-none');
            $('#generateChart').prop('disabled', true);
        } else {
            $('#loadingSpinner').addClass('d-none');
            validateForm(); // 重新验证表单以启用/禁用按钮
        }
    }
    
    /**
     * 更新图表信息
     */
    function updateChartInfo(stockCount, indexName) {
        if (stockCount > 0) {
            $('#chartInfo').text(`${stockCount}只股票 + ${indexName}`).show();
        } else {
            $('#chartInfo').hide();
        }
    }
    
    /**
     * 显示提示消息
     */
    function showAlert(message, type) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // 移除现有的alert
        $('.alert').remove();
        
        // 添加新的alert
        $('#chartForm').after(alertHtml);
        
        // 3秒后自动隐藏成功和信息类型的alert
        if (type === 'success' || type === 'info') {
            setTimeout(() => {
                $('.alert').fadeOut();
            }, 3000);
        }
    }
    
    /**
     * 简单的拼音首字母匹配函数
     */
    function matchPinyinInitials(text, searchTerm) {
        // 简单的拼音首字母映射（常用汉字）
        const pinyinMap = {
            '上': 's', '海': 'h', '电': 'd', '力': 'l', '贵': 'g', '州': 'z', '茅': 'm', '台': 't',
            '中': 'z', '国': 'g', '银': 'y', '行': 'x', '工': 'g', '商': 's', '农': 'n', '业': 'y',
            '建': 'j', '设': 's', '交': 'j', '通': 't', '民': 'm', '生': 's', '招': 'z', '发': 'f',
            '展': 'z', '万': 'w', '科': 'k', '技': 'j', '华': 'h', '为': 'w', '联': 'l', '想': 'x',
            '京': 'j', '东': 'd', '阿': 'a', '里': 'l', '巴': 'b', '腾': 't', '讯': 'x', '美': 'm',
            '团': 't', '滴': 'd', '出': 'c', '安': 'a', '全': 'q', '保': 'b', '险': 'x', '平': 'p',
            '五': 'w', '粮': 'l', '液': 'y', '泸': 'l', '老': 'l', '窖': 'j', '剑': 'j', '南': 'n',
            '春': 'c', '药': 'y', '恒': 'h', '瑞': 'r', '医': 'y', '迈': 'm', '宝': 'b', '能': 'n',
            '源': 'y', '新': 'x', '光': 'g', '伏': 'f', '钢': 'g', '铁': 't', '有': 'y', '色': 's',
            '金': 'j', '属': 's', '煤': 'm', '炭': 't', '石': 's', '油': 'y', '化': 'h', '环': 'h',
            '境': 'j', '水': 's', '务': 'w', '食': 's', '品': 'p', '饮': 'y', '料': 'l', '纺': 'f',
            '织': 'z', '服': 'f', '装': 'z', '家': 'j', '具': 'j', '电': 'd', '器': 'q', '汽': 'q',
            '车': 'c', '航': 'h', '空': 'k', '运': 'y', '输': 's', '港': 'g', '口': 'k', '机': 'j',
            '场': 'c', '房': 'f', '地': 'd', '产': 'c', '建': 'j', '筑': 'z', '材': 'c', '装': 'z',
            '修': 'x', '通': 't', '信': 'x', '计': 'j', '算': 's', '软': 'r', '件': 'j', '互': 'h',
            '联': 'l', '网': 'w', '传': 'c', '媒': 'm', '文': 'w', '化': 'h', '教': 'j', '育': 'y',
            '旅': 'l', '游': 'y', '酒': 'j', '店': 'd', '餐': 'c', '饮': 'y', '零': 'l', '售': 's'
        };
        
        // 生成拼音首字母
        let initials = '';
        for (let char of text) {
            if (pinyinMap[char]) {
                initials += pinyinMap[char];
            }
        }
        
        // 检查是否匹配
        return initials.includes(searchTerm);
    }
    
    /**
     * 工具函数：格式化数字
     */
    function formatNumber(num) {
        if (num >= 1e9) {
            return (num / 1e9).toFixed(1) + 'B';
        }
        if (num >= 1e6) {
            return (num / 1e6).toFixed(1) + 'M';
        }
        if (num >= 1e3) {
            return (num / 1e3).toFixed(1) + 'K';
        }
        return num.toString();
    }
    
    /**
     * 工具函数：格式化日期
     */
    function formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('zh-CN');
    }
    
    // 全局错误处理
    window.addEventListener('error', function(e) {
        console.error('全局错误:', e.error);
        if (!isLoading) {
            showAlert('应用出现错误，请刷新页面', 'danger');
        }
    });
    
    // 阻止表单默认提交
    $('#chartForm').on('submit', function(e) {
        e.preventDefault();
        generateChart();
    });
    
    console.log('📊 交互式股票图表应用初始化完成');
});
