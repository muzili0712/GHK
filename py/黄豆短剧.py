# -*- coding: utf-8 -*-
"""
黄豆短剧爬虫
站点: https://www.hdmgdj.com
"""

import json
import urllib.parse

import requests

try:
    from base.spider import Spider as BaseSpider
except ImportError:
    class BaseSpider:
        pass


class Spider(BaseSpider):
    """黄豆短剧爬虫"""

    BASE_URL = 'https://www.hdmgdj.com'
    API_BASE = 'https://hdmgdj.com/api'

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.hdmgdj.com/',
        'Origin': 'https://www.hdmgdj.com',
    }

    _filter_cache = {}  # 分类筛选缓存

    def __init__(self):
        super().__init__()
        self.name = ""
        self.error_play_url = "https://kjjsaas-sh.oss-cn-shanghai.aliyuncs.com/u/3401405881/20240818-936952-fc31b16575e80a7562cdb1f81a39c6b0.mp4"
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    # ==================== 标准接口 ====================

    def init(self, extend="{}"):
        """初始化"""
        if extend:
            try:
                self.extend = json.loads(extend)
                if 'name' in self.extend:
                    self.name = self.extend['name']
                if 'base_url' in self.extend:
                    self.BASE_URL = self.extend['base_url']
                    self.API_BASE = self.extend['base_url'] + '/api'
            except Exception as e:
                print(e)
        return None

    def getName(self):
        """获取爬虫名称"""
        return "黄豆短剧"

    def homeContent(self, filter):
        """首页"""
        result = {
            "class": [],
            "filters": {},
            "list": [],
            "parse": 0,
            "jx": 0,
        }

        try:
            # 获取分类
            genres_data = self._get('/genres')
            if genres_data and isinstance(genres_data, list):
                for g in genres_data:
                    gid = str(g.get('id', ''))
                    if not gid:
                        continue
                    result["class"].append({
                        "type_id": gid,
                        "type_name": g.get('name', ''),
                    })

            # 获取首页推荐
            home_data = self._get('/home')
            if home_data and isinstance(home_data, dict):
                # guess 猜你喜欢
                guess_list = home_data.get('guess', [])
                if isinstance(guess_list, list):
                    for item in guess_list:
                        result["list"].append(self._parse_vod(item))

                # feature 精选
                feature_list = home_data.get('feature', [])
                if isinstance(feature_list, list):
                    for item in feature_list:
                        result["list"].append(self._parse_vod(item))

                # 如果列表为空，用首页第一页数据
                if not result["list"]:
                    dramas_data = self._get('/dramas?page=1&size=20')
                    if dramas_data and isinstance(dramas_data, dict):
                        for item in dramas_data.get('list', []):
                            result["list"].append(self._parse_vod(item))

        except Exception as e:
            print(e)

        return result

    def categoryContent(self, tid, pg, filter, extend):
        """分类页"""
        result = {
            "page": pg,
            "pagecount": 999,
            "limit": 20,
            "total": 99999,
            "list": [],
            "parse": 0,
            "jx": 0,
        }

        try:
            # 分类ID是genre id
            data = self._get(f'/dramas?genreId={tid}&page={pg}&size=20')
            if data and isinstance(data, dict):
                lst = data.get('list', [])
                total = data.get('total', 0)
                result["total"] = total
                result["pagecount"] = (total + 19) // 20 if total else 999
                for item in lst:
                    result["list"].append(self._parse_vod(item))

        except Exception as e:
            print(e)

        return result

    def detailContent(self, ids):
        """详情页"""
        result = {
            "list": [],
            "parse": 0,
            "jx": 0,
        }

        try:
            vid = ids[0]
            data = self._get(f'/dramas/{vid}')

            if data and isinstance(data, dict):
                episodes = data.get('episodes', [])

                # 组装播放地址
                play_url_parts = []
                for ep in episodes:
                    ep_title = ep.get('title', f"第{ep.get('ep', 0)}集")
                    play_url = ep.get('playUrl', '')
                    if play_url:
                        play_url_parts.append(f"{ep_title}${play_url}")

                vod = {
                    "vod_id": str(data['id']),
                    "vod_name": data.get('t', ''),
                    "vod_pic": data.get('cover', ''),
                    "type_name": data.get('sub', ''),
                    "vod_year": '',
                    "vod_area": '',
                    "vod_remarks": f"{data.get('serial', '')}·{data.get('plays', '')}播放",
                    "vod_actor": '',
                    "vod_director": '黄豆',
                    "vod_content": data.get('summary', '') or data.get('t', ''),
                    "vod_play_from": '黄豆短剧',
                    "vod_play_url": '#'.join(play_url_parts),
                }
                result["list"].append(vod)

        except Exception as e:
            print(e)

        return result

    def searchContent(self, key, quick, pg="1"):
        """搜索"""
        result = {
            "page": pg,
            "pagecount": 999,
            "limit": 20,
            "total": 99999,
            "list": [],
            "parse": 0,
            "jx": 0,
        }

        try:
            data = self._get(f'/search?kw={urllib.parse.quote(key)}&page={pg}&size=20')
            if data and isinstance(data, dict):
                lst = data.get('list', [])
                total = data.get('total', 0)
                result["total"] = total
                result["pagecount"] = (total + 19) // 20 if total else 0
                for item in lst:
                    result["list"].append(self._parse_vod(item))

        except Exception as e:
            print(e)

        return result

    def playerContent(self, flag, id, vipFlags):
        """播放页 - 直接返回 m3u8 data URI"""
        result = {
            "parse": 0,
            "playUrl": "",
            "url": self.error_play_url,
            "jx": 0,
            "header": "",
        }

        if id:
            # 直接在 playerContent 里生成解密后的 m3u8，用 data URI 返回
            # 这样播放地址就不是 127.0.0.1 代理了
            m3u8_content = self._build_m3u8_with_key(id)
            if m3u8_content:
                import base64
                m3u8_b64 = base64.b64encode(m3u8_content.encode('utf-8')).decode('ascii')
                result["url"] = "data:application/vnd.apple.mpegurl;base64," + m3u8_b64
                result["parse"] = 0

        return result

    def _build_m3u8_with_key(self, url):
        """构建 m3u8 内容（key 内嵌为 base64 data URI，ts 用原始绝对地址）"""
        import hashlib
        import re
        import base64
        if not url:
            return None

        try:
            r = self.session.get(url, timeout=15, verify=False)
            content = r.text

            # 计算 key
            key_bytes = self._get_key_bytes(url)
            if key_bytes:
                key_b64 = base64.b64encode(key_bytes).decode('ascii')
                key_data_uri = "data:text/plain;base64," + key_b64
                content = re.sub(
                    r'(#EXT-X-KEY:.*?URI=")[^"]*(")',
                    r'\1' + key_data_uri + r'\2',
                    content
                )

            # 把相对路径的 ts 改成绝对路径
            base_url = url.rsplit('/', 1)[0] + '/'
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    if line.startswith('http'):
                        new_lines.append(line)
                    else:
                        new_lines.append(base_url + line)
                else:
                    new_lines.append(line)
            content = '\n'.join(new_lines)
            return content
        except Exception as e:
            print(f"_build_m3u8_with_key error: {e}")
            return None

    def _get_key_bytes(self, url):
        """从 m3u8 URL 计算解密 key"""
        import hashlib
        import re
        m = re.search(r'/hls/([0-9a-f]{64})/', url)
        if not m:
            return None
        video_id = m.group(1)
        ver_match = re.search(r'[?&]version=([^&#]+)', url)
        version = ver_match.group(1) if ver_match else 'v1'
        prefix = "xnaichanping"
        key_str = prefix + video_id + version
        return hashlib.md5(key_str.encode()).digest()

    def localProxy(self, params):
        """本地代理 - 处理海报图片解密"""
        try:
            do = params.get('do', '')
            if do == 'img':
                url = params.get('url', '')
                if not url:
                    return 0
                return self._decrypt_image(url)
        except Exception as e:
            print(f"localProxy error: {e}")
        return 0

    def _decrypt_image(self, url):
        """解密加密的海报图片"""
        import hashlib
        import re
        try:
            r = self.session.get(url, timeout=15, verify=False)
            encrypted = r.content

            # 提取 imageId (64位哈希)
            m = re.search(r'([0-9a-f]{64})', url)
            if not m:
                return [200, "image/png", {}, encrypted]

            image_id = m.group(1)

            # 提取 version
            ver_match = re.search(r'[?&]version=([^&#]+)', url)
            version = ver_match.group(1) if ver_match else 'v1'

            # 计算解密 key
            prefix = "xnaichanping"
            key_str = prefix + image_id + version
            key_bytes = hashlib.md5(key_str.encode()).digest()

            # AES-128-CBC 解密，IV=0
            from Crypto.Cipher import AES
            iv = bytes.fromhex('00000000000000000000000000000000')
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
            decrypted = cipher.decrypt(encrypted)

            # 去掉 PKCS7 padding
            pad_len = decrypted[-1]
            if 1 <= pad_len <= 16:
                decrypted = decrypted[:-pad_len]

            # 确定图片类型
            content_type = "image/png"
            if decrypted[:3] == b'\xff\xd8\xff':
                content_type = "image/jpeg"
            elif decrypted[:8] == b'\x89PNG\r\n\x1a\n':
                content_type = "image/png"
            elif decrypted[:6] == b'GIF87a' or decrypted[:6] == b'GIF89a':
                content_type = "image/gif"
            elif decrypted[:4] == b'RIFF' and decrypted[8:12] == b'WEBP':
                content_type = "image/webp"

            return [200, content_type, {}, decrypted]
        except Exception as e:
            print(f"_decrypt_image error: {e}")
            return 0

    # ==================== 内部方法 ====================

    def _parse_vod(self, item):
        """解析视频条目"""
        return {
            "vod_id": str(item['id']),
            "vod_name": item.get('t', ''),
            "vod_pic": item.get('cover', ''),
            "vod_remarks": f"{item.get('serial', '')}·{item.get('eps', 0)}集",
        }

    def _get(self, path):
        """发送 GET 请求"""
        url = self.API_BASE + path
        try:
            r = self.session.get(url, timeout=15, verify=False)
            resp = r.json()
            if resp.get('code') == 0 and resp.get('data') is not None:
                return resp['data']
            return None
        except Exception as e:
            print(e)
            return None


# 调试用
if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    s = Spider()
    s.init()

    print('=== 首页 ===')
    home = s.homeContent(True)
    print(f'分类: {len(home["class"])}个')
    for c in home['class']:
        print(f'  {c["type_id"]}: {c["type_name"]}')
    print(f'推荐: {len(home["list"])}个')
    for v in home['list'][:5]:
        print(f'  {v["vod_id"]}: {v["vod_name"]} - {v["vod_remarks"]}')
    print()

    print('=== 分类1（都市）第1页 ===')
    cr = s.categoryContent('1', 1, True, {})
    print(f'总数: {cr["total"]}, 本页: {len(cr["list"])}个')
    for v in cr['list'][:5]:
        print(f'  {v["vod_id"]}: {v["vod_name"]}')
    print()

    print('=== 搜索 穿越 ===')
    sr = s.searchContent('穿越', False, '1')
    print(f'结果: {len(sr["list"])}个, 总数: {sr["total"]}')
    for v in sr['list'][:5]:
        print(f'  {v["vod_id"]}: {v["vod_name"]}')
    print()

    if sr['list']:
        vid = sr['list'][0]['vod_id']
        print(f'=== 详情 {vid} ===')
        dr = s.detailContent([vid])
        if dr['list']:
            v = dr['list'][0]
            print(f'标题: {v["vod_name"]}')
            print(f'分类: {v["type_name"]}')
            print(f'备注: {v["vod_remarks"]}')
            print(f'播放源: {v["vod_play_from"]}')
            play_urls = v["vod_play_url"].split('#')
            print(f'集数: {len(play_urls)}集')
            print(f'第一集: {play_urls[0][:80]}...')
