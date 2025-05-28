from flask import Flask, request, jsonify, render_template # ❗这里把 render_template_string 改成了 render_template
from DrissionPage import ChromiumPage, ChromiumOptions
from urllib.parse import urlparse, parse_qs
import json

app = Flask(__name__)

# ❗❗❗ HTML_TEMPLATE 变量及其内容已移除，现在 HTML 内容在 templates/index.html 文件中 ❗❗❗

@app.route('/')
def index():
    # ❗❗❗ Flask 会自动在 'templates' 文件夹中寻找 'index.html' 文件
    return render_template('index.html')


@app.route('/get_video_url', methods=['GET'])
def get_video_url():
    # 从请求参数中获取抖音链接
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400

    # 后端：去除 URL 两端的空格，确保处理任何来源的输入
    url = url.strip()

    browser = None
    try:
        co = ChromiumOptions().headless()  # 保持 headless 模式

        # ！！！！！！ 只保留了 Docker 运行环境相关的三个参数 ！！！！！！
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-gpu')

        print("已配置浏览器参数：--no-sandbox, --disable-dev-shm-usage, --disable-gpu")

        print("正在创建浏览器实例...")
        browser = ChromiumPage(co)
        print("浏览器实例创建成功")

        print(f"原始输入URL (处理后): {url}")
        browser.get(url)

        current_url = browser.url
        print(f"重定向后的URL: {current_url}")

        video_id = None
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)

        if 'vid' in query_params and query_params['vid']:
            video_id = query_params['vid'][0]
            print(f"提取到视频ID: {video_id}")
        elif 'video' in parsed_url.path:
            path_parts = parsed_url.path.split('/')
            if len(path_parts) > 2 and path_parts[-2] == 'video':
                video_id = path_parts[-1]
                print(f"从路径中提取到视频ID: {video_id}")

        if not video_id:
            raise Exception(f"无法从抖音链接中提取到视频ID。当前URL: {current_url}")

        detail_url = f"https://www.douyin.com/video/{video_id}"
        print(f"构造详情页URL: {detail_url}")

        print("开始监听网络请求...")
        browser.listen.start(r'/aweme/v1/web/aweme/detail/')
        print("网络监听已启动")

        print(f"正在访问详情页: {detail_url}")
        browser.get(detail_url)
        print("详情页访问完成，等待API响应...")

        resp = browser.listen.wait()

        json_data = resp.response.body


        aweme_detail = json_data.get('aweme_detail')
        video_info = aweme_detail.get('video', {})
        play_addr = video_info.get('play_addr', {})
        url_list = play_addr.get('url_list', [])

        if not url_list:
            raise Exception("未找到视频播放地址 (url_list)。")

        video_url = ''
        # 使用你之前成功代码中的逻辑，优先获取第三个，否则获取第一个并替换'playwm'
        if len(url_list) > 2:
            video_url = url_list[2].replace('playwm', 'play')
        elif len(url_list) > 0:
            video_url = url_list[0].replace('playwm', 'play')

        if not video_url:
            raise Exception("无法获取有效的视频播放地址。")

        print(f"成功获取视频URL: {video_url}")
        return jsonify({'video_url': video_url})

    except Exception as e:
        error_msg = str(e)
        print(f"解析过程中出错: {error_msg}")
        return jsonify({'error': f'解析失败: {error_msg}'}), 500

    finally:
        if browser:
            try:
                print("正在关闭浏览器...")
                browser.quit()
                print("浏览器已关闭")
            except Exception as close_error:
                print(f"关闭浏览器时出错: {close_error}")
                pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)