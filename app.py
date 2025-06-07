from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from terabox1 import TeraboxFile as TF1, TeraboxLink as TL1
from terabox2 import TeraboxFile as TF2, TeraboxLink as TL2, TeraboxSession as TS
from terabox3 import TeraboxFile as TF3, TeraboxLink as TL3

app = Flask(__name__)
CORS(app)

# Load configuration
with open('config.json') as config_file:
    config = json.load(config_file)

@app.route('/')
def home():
    """API Documentation"""
    base_url = request.url_root
    return jsonify({
        'status': 'success',
        'endpoints': {
            'get_config': {
                'method': 'GET',
                'url': f'{base_url}get_config',
                'description': 'Get current configuration'
            },
            'generate_file': {
                'method': 'GET',
                'url': f'{base_url}generate_file',
                'parameters': {'url': 'Terabox share URL'},
                'description': 'Get file information from Terabox URL'
            },
            'generate_link': {
                'method': 'GET',
                'url': f'{base_url}generate_link',
                'parameters': {
                    'fs_id': 'File ID',
                    'uk': 'User ID',
                    'shareid': 'Share ID',
                    'timestamp': 'Timestamp',
                    'sign': 'Signature',
                    'js_token': 'JS Token (mode 1 only)',
                    'cookie': 'Cookie (mode 1 only)'
                },
                'description': 'Generate download links'
            }
        }
    })

@app.route('/get_config', methods=['GET'])
def get_config():
    """Get current configuration"""
    try:
        session = TS()
        session.generateCookie()
        session.generateAuth()
        if session.isLogin:
            return jsonify({
                'status': 'success',
                'mode': config.get('mode', 3),
                'cookie': config.get('cookie', ''),
                'user_id': config.get('user_id', 'null')
            })
        return jsonify({
            'status': 'error',
            'message': 'Invalid Terabox cookie',
            'mode': config.get('mode', 3)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'mode': config.get('mode', 3)
        })

@app.route('/generate_file', methods=['GET'])
def generate_file():
    """Get file information from Terabox URL"""
    url = request.args.get('url')
    if not url:
        return jsonify({'status': 'error', 'message': 'URL parameter is required'})
    
    try:
        mode = config.get('mode', 3)
        cookie = config.get('cookie', '')
        
        if mode == 1:
            tf = TF1()
        elif mode == 2:
            tf = TF2(cookie)
        else:  # mode 3
            tf = TF3()
            
        tf.search(url)
        return jsonify(tf.result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/generate_link', methods=['GET'])
def generate_link():
    """Generate download links"""
    mode = config.get('mode', 3)
    
    if mode == 1:
        required_params = ['fs_id', 'uk', 'shareid', 'timestamp', 'sign', 'js_token', 'cookie']
        params = {p: request.args.get(p) for p in required_params}
        if None in params.values():
            missing = [p for p in required_params if params[p] is None]
            return jsonify({'status': 'error', 'message': f'Missing parameters: {", ".join(missing)}'})
        
        tl = TL1(**params)
        tl.generate()
        return jsonify(tl.result)
    
    elif mode == 2:
        url = request.args.get('url')
        if not url:
            return jsonify({'status': 'error', 'message': 'URL parameter is required'})
        
        tl = TL2(url)
        return jsonify(tl.result)
    
    elif mode == 3:
        required_params = ['fs_id', 'uk', 'shareid', 'timestamp', 'sign']
        params = {p: request.args.get(p) for p in required_params}
        if None in params.values():
            missing = [p for p in required_params if params[p] is None]
            return jsonify({'status': 'error', 'message': f'Missing parameters: {", ".join(missing)}'})
        
        tl = TL3(**params)
        tl.generate()
        return jsonify(tl.result)
    
    else:
        return jsonify({'status': 'error', 'message': 'Invalid mode in configuration'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)