import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm';
import { AvatarController, moodForResponse, measureFraming, fitCamera } from './avatar.js';

const API_URL = 'http://127.0.0.1:5000/chat';
const MODEL_URL = '/models/avatar.vrm'; 
const TYPE_CPS = 60;                 

const container = document.getElementById('avatar-container');
const statusEl = document.getElementById('avatar-status');
const chatWindow = document.getElementById('chat-window');
const input = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

function setStatus(text) {
  statusEl.textContent = text;
}

let renderer = null;
let scene = null;
let camera = null;
let controller = null;
let framing = null; 

function applyFraming() {
  if (!framing || !camera) return;
  const { y, dist } = fitCamera(framing, camera.fov, camera.aspect);
  camera.position.set(0, y, dist);
  camera.lookAt(0, y, 0);
}

function resize() {
  if (!renderer) return;
  const w = Math.max(container.clientWidth, 1);
  const h = Math.max(container.clientHeight, 1);
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  applyFraming();
}

function initScene() {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  container.appendChild(renderer.domElement);

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(30, 1, 0.1, 20);
  camera.position.set(0, 1.25, 1.4);

  const light = new THREE.DirectionalLight(0xffffff, Math.PI);
  light.position.set(1, 1, 1).normalize();
  scene.add(light);

  resize();
  if (typeof ResizeObserver !== 'undefined') {
    new ResizeObserver(resize).observe(container);
  } else {
    window.addEventListener('resize', resize);
  }

  let last = performance.now();
  renderer.setAnimationLoop((now) => {
    const dt = (now - last) / 1000;
    last = now;
    if (controller) controller.update(dt);
    renderer.render(scene, camera);
  });
}

function loadAvatar() {
  const loader = new GLTFLoader();
  loader.register((parser) => new VRMLoaderPlugin(parser));

  loader.load(
    MODEL_URL,
    (gltf) => {
      const vrm = gltf.userData.vrm;
      if (!vrm) {
        setStatus('The file loaded, but it is not a VRM model.');
        return;
      }
      VRMUtils.removeUnnecessaryVertices(gltf.scene);
      VRMUtils.combineSkeletons(gltf.scene);
      VRMUtils.rotateVRM0(vrm); 
      vrm.scene.traverse((obj) => {
        obj.frustumCulled = false;
      });
      scene.add(vrm.scene);

      controller = new AvatarController(vrm, camera);
      controller.update(0.016); 
      framing = measureFraming(vrm);
      applyFraming();
      controller.setMood('greeting', 3);
      setStatus('');
    },
    (event) => {
      if (event.total) {
        const pct = Math.round((event.loaded / event.total) * 100);
        const mb = (event.loaded / (1024 * 1024)).toFixed(0);
        setStatus(`Loading avatar... ${pct}% (${mb} MB)`);
      } else {
        setStatus('Loading avatar...');
      }
    },
    (error) => {
      console.error('Avatar failed to load:', error);
      setStatus(`Could not load ${MODEL_URL}. Check that the file is in public/models/.`);
    }
  );
}

try {
  initScene();
  loadAvatar();
} catch (err) {
  console.error('3D avatar unavailable:', err);
  setStatus('3D avatar unavailable (WebGL could not start). The chat still works.');
}

let busy = false;

function setBusy(value) {
  busy = value;
  input.disabled = value;
  sendBtn.disabled = value;
  if (!value) input.focus();
}

function addMessage(prefix, text) {
  const div = document.createElement('div');
  div.className = prefix === 'You' ? 'msg user' : 'msg bot';
  div.textContent = `${prefix}: ${text}`;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return div;
}

function typeInto(div, prefix, text) {
  return new Promise((resolve) => {
    if (controller) controller.talkFor(text.length / TYPE_CPS + 0.3);
    const start = performance.now();
    const timer = setInterval(() => {
      const shown = Math.min(text.length, Math.floor(((performance.now() - start) / 1000) * TYPE_CPS));
      div.textContent = `${prefix}: ${text.slice(0, shown)}`;
      chatWindow.scrollTop = chatWindow.scrollHeight;
      if (shown >= text.length) {
        clearInterval(timer);
        resolve();
      }
    }, 30);
  });
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text || busy) return;

  setBusy(true);
  addMessage('You', text);
  input.value = '';

  let data;
  try {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    if (!res.ok) throw new Error(`Server returned ${res.status}`);
    data = await res.json();
  } catch (err) {
    console.error(err);
    data = { reply: 'Error connecting to the chatbot server.', intent: 'error', confidence: 1 };
  }

  if (controller) controller.setMood(moodForResponse(data), 5);
  const line = addMessage('Bot', '');
  await typeInto(line, 'Bot', data.reply);
  setBusy(false);
}

sendBtn.addEventListener('click', sendMessage);
input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendMessage();
});
