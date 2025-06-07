const apiBaseUrl = 'http://192.168.58.5:5000'; // Your Flask API endpoint
let videoPlayer;
let currentFiles = [];

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Video.js player
    videoPlayer = videojs('terabox-player', {
        controls: true,
        autoplay: false,
        preload: 'auto',
        responsive: true,
        fluid: true
    });
    
    // Set up event listeners
    document.getElementById('submit_button').addEventListener('click', handleSearch);
    document.getElementById('terabox_url').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });
});

async function handleSearch() {
    const url = document.getElementById('terabox_url').value.trim();
    if (!url) return;

    try {
        showLoading(true);
        clearResults();
        
        // Fetch file list from API
        const files = await fetchFiles(url);
        currentFiles = files;
        
        if (files.length > 0) {
            displayFiles(files);
        } else {
            showMessage('No video files found in this link');
        }
    } catch (error) {
        showMessage('Error: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function fetchFiles(url) {
    const response = await fetch(`${apiBaseUrl}/generate_file?url=${encodeURIComponent(url)}`);
    const data = await response.json();
    
    if (data.status !== 'success') {
        throw new Error(data.message || 'Failed to fetch files');
    }
    
    // Extract all video files recursively
    const extractVideos = (items) => {
        return items.reduce((acc, item) => {
            if (item.is_dir === "1") {
                return [...acc, ...extractVideos(item.list)];
            } else if (item.type === "video") {
                return [...acc, {
                    ...item,
                    shareid: data.shareid,
                    uk: data.uk,
                    sign: data.sign,
                    timestamp: data.timestamp
                }];
            }
            return acc;
        }, []);
    };
    
    return extractVideos(data.list);
}

function displayFiles(files) {
    const fileList = document.getElementById('file-list');
    fileList.innerHTML = '';
    
    files.forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <div class="file-info">
                <div class="file-thumbnail" style="background-image: url('${file.image || ''}')"></div>
                <div class="file-details">
                    <h3>${file.name}</h3>
                    <p>${formatFileSize(file.size)}</p>
                </div>
                <div class="file-actions">
                    <button class="play-button" data-fs-id="${file.fs_id}">
                        <i class="fas fa-play"></i> Play
                    </button>
                    <button class="download-button" data-fs-id="${file.fs_id}">
                        <i class="fas fa-download"></i> Download
                    </button>
                </div>
            </div>
        `;
        fileList.appendChild(fileItem);
        
        // Add event listeners
        fileItem.querySelector('.play-button').addEventListener('click', () => playVideo(file));
        fileItem.querySelector('.download-button').addEventListener('click', () => downloadFile(file));
    });
}

async function playVideo(file) {
    try {
        showLoading(true, 'Preparing video...');
        
        // Get the streaming URL
        const streamUrl = await getStreamUrl(file);
        
        // Set up the video player
        videoPlayer.poster(file.image || '');
        videoPlayer.src({
            src: streamUrl,
            type: 'video/mp4'
        });
        
        // Show the player
        document.getElementById('video-container').style.display = 'block';
        videoPlayer.play();
    } catch (error) {
        showMessage('Error playing video: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function getStreamUrl(file) {
    const params = new URLSearchParams({
        shareid: file.shareid,
        uk: file.uk,
        sign: file.sign,
        timestamp: file.timestamp,
        fs_id: file.fs_id
    });
    
    const response = await fetch(`${apiBaseUrl}/generate_link?${params}`);
    const data = await response.json();
    
    if (data.status !== 'success') {
        throw new Error(data.message || 'Failed to get stream URL');
    }
    
    // Always use url_2 if available
    return data.download_link.url_2 || data.download_link.url_1;
}

async function downloadFile(file) {
    try {
        showLoading(true, 'Preparing download...');
        const downloadUrl = await getStreamUrl(file);
        
        // Create a temporary anchor element to trigger download
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = file.name;
        a.target = '_blank';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    } catch (error) {
        showMessage('Error downloading file: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function formatFileSize(bytes) {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showLoading(show, message = '') {
    const submitBtn = document.getElementById('submit_button');
    if (show) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = message ? `${message} <div class="spinner"></div>` : '<div class="spinner"></div>';
    } else {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Search';
    }
}

function showMessage(message) {
    const fileList = document.getElementById('file-list');
    fileList.innerHTML = `<div class="message">${message}</div>`;
}

function clearResults() {
    document.getElementById('file-list').innerHTML = '';
    document.getElementById('video-container').style.display = 'none';
    videoPlayer.pause();
    videoPlayer.src('');
}
