const SRS_WEBRTC_URL = 'http://localhost:1985/rtc/v1/whep/';

export class AvatarWebRTCClient {
  constructor(options = {}) {
    this.pc = null;
    this.sdk = null;
    this.stream = null;
    this.status = 'disconnected';
    this.url = options.url || SRS_WEBRTC_URL;
    this.streamName = options.streamName || 'livestream';
    this.onTrack = options.onTrack || null;
    this.onStatusChange = options.onStatusChange || null;
  }

  async connect() {
    if (this.status === 'connected' || this.status === 'connecting') {
      console.warn('[WebRTC] Already connected or connecting');
      return;
    }

    this._updateStatus('connecting');

    try {
      this.pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
        bundlePolicy: 'max-compat',
        rtcpMuxPolicy: 'negotiate'
      });

      this.pc.ontrack = (event) => {
        console.log('[WebRTC] Received remote track:', event.track.kind);
        this.stream = event.streams[0];
        if (this.onTrack) {
          this.onTrack(event.streams[0], event.track.kind);
        }
      };

      this.pc.oniceconnectionstatechange = () => {
        console.log('[WebRTC] ICE state:', this.pc.iceConnectionState);
        if (this.pc.iceConnectionState === 'connected') {
          this._updateStatus('connected');
        } else if (this.pc.iceConnectionState === 'disconnected' || this.pc.iceConnectionState === 'failed') {
          this._updateStatus('disconnected');
        }
      };

      const offer = await this.pc.createOffer({
        offerToReceiveAudio: true,
        offerToReceiveVideo: true
      });
      await this.pc.setLocalDescription(offer);

      const response = await fetch(`${this.url}?app=live&stream=${this.streamName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sdp: this.pc.localDescription.sdp, type: 'offer' })
      });

      if (!response.ok) {
        throw new Error(`WebRTC signaling failed: ${response.status}`);
      }

      const answer = await response.json();
      await this.pc.setRemoteDescription(new RTCSessionDescription({
        type: 'answer',
        sdp: answer.sdp
      }));

    } catch (error) {
      console.error('[WebRTC] Connection error:', error);
      this._updateStatus('disconnected');
      this.disconnect();
      throw error;
    }
  }

  disconnect() {
    if (this.pc) {
      this.pc.close();
      this.pc = null;
    }
    this.stream = null;
    this._updateStatus('disconnected');
  }

  _updateStatus(status) {
    this.status = status;
    if (this.onStatusChange) {
      this.onStatusChange(status);
    }
  }

  getVideoElement() {
    return this.stream;
  }
}

export async function createAvatarStream(videoElement) {
  return new Promise((resolve, reject) => {
    const pc = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    });

    pc.ontrack = (event) => {
      videoElement.srcObject = event.streams[0];
      resolve(pc);
    };

    pc.createOffer({
      offerToReceiveAudio: true,
      offerToReceiveVideo: true
    }).then(offer => pc.setLocalDescription(offer)).then(() => {
      fetch('http://localhost:1985/rtc/v1/whip/?app=live&stream=livestream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sdp: pc.localDescription.sdp, type: 'offer' })
      }).then(res => res.json()).then(answer => {
        pc.setRemoteDescription(new RTCSessionDescription(answer));
      }).catch(reject);
    }).catch(reject);
  });
}

export default AvatarWebRTCClient;