import re, requests, base64, random, cloudscraper
from urllib.parse import quote

headers : dict[str, str] = {'user-agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36'}

class TeraboxFile():

    #--> Initialization (requests, headers, and result)
    def __init__(self) -> None:

        self.r : object = requests.Session()
        self.sc = cloudscraper.create_scraper()
        self.headers : dict[str,str] = headers
        self.result : dict[str,any] = {'status':'failed', 'sign':'', 'timestamp':'', 'shareid':'', 'uk':'', 'list':[]}

    #--> Main control (get short_url, init authorization, and get root file)
    def search(self, url:str) -> None:

        req : str = self.r.get(url, allow_redirects=True)
        self.short_url : str = re.search(r'surl=([^ &]+)',str(req.url)).group(1)
        self.getMainFile()
        self.getSign()

    #--> Get sign & timestamp from 'https://terabox.hnn.workers.dev/'
    def getSign(self) -> None:

        api = 'https://terabox.hnn.workers.dev/api/get-info'
        post_url = f'{api}?shorturl={self.short_url}&pwd='
        
        headers_post : dict[str,str] = {
            'accept-language':'en-US,en;q=0.9,id;q=0.8',
            'referer':'https://terabox.hnn.workers.dev/',
            'sec-fetch-mode':'cors',
            'sec-fetch-site':'same-origin',
            'user-agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36',
        }
        
        try:
            self.sc = cloudscraper.create_scraper()
            pos = self.sc.get(post_url, headers=headers_post, allow_redirects=True).json()
            if pos['ok']:
                self.result['sign']      = pos['sign']
                self.result['timestamp'] = pos['timestamp']
                self.result['status']    = 'success'
            else: self.result['status']  = 'failed'
        except Exception: self.result['status'] = 'failed'

    #--> Get payload (root / top layer / overall data) and init packing file information
    def getMainFile(self) -> None:

        url: str = f'https://www.terabox.com/api/shorturlinfo?app_id=250528&shorturl=1{self.short_url}&root=1'
        req : object = self.r.get(url, headers=self.headers, cookies={'cookie':''}).json()
        all_file = self.packData(req, self.short_url)
        if len(all_file):
            self.result['shareid']   = req['shareid']
            self.result['uk']        = req['uk']
            self.result['list']      = all_file

    #--> Get child file data recursively (if any) and init packing file information
    def getChildFile(self, short_url, path:str='', root:str='0') -> list[dict[str, any]]:

        params = {'app_id':'250528', 'shorturl':short_url, 'root':root, 'dir':path}
        url = 'https://www.terabox.com/share/list?' + '&'.join([f'{a}={b}' for a,b in params.items()])
        req : object = self.r.get(url, headers=self.headers, cookies={'cookie':''}).json()
        return(self.packData(req, short_url))

    #--> Pack each file information
    def packData(self, req:dict, short_url:str) -> list[dict[str, any]]:
        all_file = [{
            'is_dir' : item['isdir'],
            'path'   : item['path'],
            'fs_id'  : item['fs_id'],
            'name'   : item['server_filename'],
            'type'   : self.checkFileType(item['server_filename']) if not bool(int(item.get('isdir'))) else 'other',
            'size'   : item.get('size') if not bool(int(item.get('isdir'))) else '',
            'image'  : item.get('thumbs',{}).get('url3','') if not bool(int(item.get('isdir'))) else '',
            'list'   : self.getChildFile(short_url, item['path'], '0') if item.get('isdir') else [],
        } for item in req.get('list', [])]
        return(all_file)

    # Check Format File
    def checkFileType(self, name:str) -> str:
        name = name.lower()
        if any(ext in name for ext in ['.mp4', '.mov', '.m4v', '.mkv', '.asf', '.avi', '.wmv', '.m2ts', '.3g2']):
            typefile = 'video'
        elif any(ext in name for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
            typefile = 'image'
        elif any(ext in name for ext in ['.pdf', '.docx', '.zip', '.rar', '.7z']):
            typefile = 'file'
        else:
            typefile = 'other'
        return(typefile)

class TeraboxLink():

    #--> Initialization (requests, headers, payload, and result)
    def __init__(self, shareid:str, uk:str, sign:str, timestamp:str, fs_id:str) -> None:

        self.domain : str = 'https://terabox.hnn.workers.dev/'
        self.api    : str = f'{self.domain}api'

        self.sc = cloudscraper.create_scraper()
        self.headers : dict[str,str] = {
            'accept-language':'en-US,en;q=0.9,id;q=0.8',
            'referer':self.domain,
            'sec-fetch-mode':'cors',
            'sec-fetch-site':'same-origin',
            'user-agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36',
        }
        self.result : dict[str,dict] = {'status':'failed', 'download_link':{}}

        #--> Params
        self.params : dict[str,any] = {
            'shareid'   : str(shareid),
            'uk'        : str(uk),
            'sign'      : str(sign),
            'timestamp' : str(timestamp),
            'fs_id'     : str(fs_id),
        }
        
        #--> List domain buat bungkus
        self.base_urls = [
            'plain-grass-58b2.comprehensiveaquamarine',
            'royal-block-6609.ninnetta7875',
            'bold-hall-f23e.7rochelle',
            'winter-thunder-0360.belitawhite',
            'fragrant-term-0df9.elviraeducational',
            'purple-glitter-924b.miguelalocal'
        ]

    #--> Generate download link
    def generate(self) -> None:

        params : dict = self.params
        
        #--> download link 1
        try:
            url_1=  f'{self.api}/get-download'
            pos_1 = self.sc.post(url_1, json=params, headers=self.headers, allow_redirects=True).json()
            self.result['download_link'].update({'url_1':pos_1['downloadLink']})
        except Exception as e: print(e)

        #--> download link 2
        try:
            url_2=  f'{self.api}/get-downloadp'
            pos_2 = self.sc.post(url_2, json=params, headers=self.headers, allow_redirects=True).json()
            self.result['download_link'].update({'url_2':self.wrap_url(pos_2['downloadLink'])})
        except Exception as e: print(e)

        if len(list(self.result['download_link'].keys())) != 0:
            self.result['status'] = 'success'
    
    #--> Bungkus url asli setelah di-quote, lalu base64
    def wrap_url(self, original_url:str) -> str:
        selected_base = random.choice(self.base_urls)
        quoted_url = quote(original_url, safe='')
        b64_encoded = base64.urlsafe_b64encode(quoted_url.encode()).decode()
        return f'https://{selected_base}.workers.dev/?url={b64_encoded}'

class Test():

    def __init__(self) -> None:
        pass

    def file(self) -> None:

        # url = 'https://1024terabox.com/s/1eBHBOzcEI-VpUGA_xIcGQg' #-> Test File Besar
        url = 'https://dm.terabox.com/indonesian/sharing/link?surl=KKG3LQ7jaT733og97CBcGg' #-> Test File All Format (Video, Gambar)
        # url = 'https://www.terabox.com/wap/share/filelist?surl=cmi8P-_NCAHAzxj7MtzZAw' #-> Test File (Zip)

        TF = TeraboxFile()
        TF.search(url)

        print(TF.result)
        open('backend/json/test_file.json', 'w', encoding='utf-8').write(str(TF.result))

    def link(self) -> None:

        #--> Standard
        fs_id     = '854989261567890'
        uk        = '4400994387999'
        shareid   = '21362218376'

        #--> Fatal
        timestamp = '1744108146'
        sign      = '19c818a0e01ad8d0131cadfe6892bc73620fbaf7'

        TL = TeraboxLink(shareid, uk, sign, timestamp, fs_id)
        TL.generate()

        print(TL.result)
        open('backend/json/test_link.json', 'w', encoding='utf-8').write(str(TL.result))

if __name__ == '__main__':

    T = Test()
    # T.file()
    # T.link()

# [ Reference ]
# https://terabox.hnn.workers.dev/
# https://github.com/NamasteIndia/Terabox-Downloader-2023