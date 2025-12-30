from playwright.sync_api import sync_playwright
import re
def extract_wrapped_content(text: str) -> str | None:
    pattern = r'>>>(.*?)<<<'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None
def scrape_huaban_pin(url: str, timeout: int = 10000) -> dict:
    """
    抓取花瓣网pin页面的内容（带反爬虫伪装）
    """
    with sync_playwright() as p:
        # 启动浏览器，添加伪装选项
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',#禁用自动化控制特征的标志
                '--disable-dev-shm-usage', # 禁用/dev/shm使用，避免内存问题，更像真实浏览器
                '--no-sandbox', # 禁用沙盒模式，某些环境下需要
                '--disable-setuid-sandbox', # 禁用setuid沙盒
                '--disable-web-security', # 禁用Web安全限制，允许跨域请求
                '--disable-features=IsolateOrigins,site-per-process' # 禁用站点隔离，减少资源占用
            ]
        )
        
        try:
            # 创建新页面，设置 User-Agent
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN',
                timezone_id='Asia/Shanghai'
            )
            
            page = context.new_page()
            
            # 添加额外的伪装脚本
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });
            """)
            
            # 访问页面
            page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            
            # 等待页面完全加载
            page.wait_for_timeout(5000)
            
            result = {
                "url": url,
                "title": "",
                "description": "",
                "image_url": "",
                "all_content": ""
            }
            
            # 1. 获取页面标题
            try:
                result["title"] = page.title()
            except:
                pass
            
            # 2. 等待#pin_detail出现
            try:
                page.wait_for_selector("#pin_detail", timeout=10000)
            except:
                print("警告: #pin_detail 未找到")
            
            # 3. 获取#pin_detail的所有内容
            pin_detail = page.query_selector("#pin_detail")
            if pin_detail:
                all_text = pin_detail.text_content()
                result["all_content"] = all_text.strip()
                
                # 4. 提取图片URL
                img = pin_detail.query_selector("img")
                if img:
                    result["image_url"] = img.get_attribute("src") or ""
                
                # 5. 提取描述（去除提示文字）
                lines = all_text.split("\n")
                description_lines = []
                for line in lines:
                    line = line.strip()
                    if line and "采集点采集" not in line and "创建你的在线" not in line:
                        description_lines.append(line)
                
                result["description"] = " ".join(description_lines).strip()
            else:
                print("未找到 #pin_detail 元素")
                
                # 尝试获取整个页面的文本
                body = page.query_selector("body")
                if body:
                    result["all_content"] = body.text_content()[:500]
            
            context.close()
            return result
            
        except Exception as e:
            print(f"抓取失败：{str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
        finally:
            browser.close()
if __name__ == "__main__":
    target_url = "https://huaban.com/pins/6094757857"
    result = scrape_huaban_pin(target_url)
    if "error" not in result:
        print(f"\n读取的关键内容:{extract_wrapped_content(result['all_content'])}")
    else:
        print(f"\n抓取失败: {result['error']}")
