import * as THREE from 'three';

export const LOW_CONFIDENCE = 0.20;

const ARM_ANGLE = 1.15;

const MOODS = {
  greeting: ['happy', 0.8],
  servant_info: ['happy', 0.7],
  event_info: ['happy', 0.6],
  game_info: ['relaxed', 0.5],
  gacha_info: ['relaxed', 0.6],
  gameplay_help: ['relaxed', 0.4],
  player_review: ['relaxed', 0.5],
  fallback: ['sad', 0.9],      
  confused: ['Surprised', 1.0], 
  error: ['sad', 1.0],         
};

const EMOTIONS = ['happy', 'relaxed', 'sad', 'angry', 'Surprised'];

const NAME_CANDIDATES = { Surprised: ['Surprised', 'surprised'] };
const VOWELS = ['aa', 'ih', 'ou', 'ee', 'oh'];
const BONES = ['spine', 'chest', 'neck', 'head', 'leftUpperArm', 'rightUpperArm'];

const rand = (a, b) => a + Math.random() * (b - a);
const approach = (cur, target, rate, dt) => cur + (target - cur) * Math.min(1, rate * dt);

export function moodForResponse(data) {
  if (data.intent === 'error') return 'error';
  switch (data.kind) {
    case 'servant': return 'servant_info';
    case 'unclear': return 'confused';
    case 'offtopic': return 'fallback';
    case 'answer': return data.intent in MOODS ? data.intent : 'game_info';
    default: break;
  }
  if (data.intent === 'servant_info') return 'servant_info';
  if (data.confidence < LOW_CONFIDENCE) return 'confused';
  return data.intent in MOODS ? data.intent : 'game_info';
}

export function measureFraming(vrm) {
  vrm.scene.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(vrm.scene);
  const head = vrm.humanoid ? vrm.humanoid.getNormalizedBoneNode('head') : null;
  const headY = head ? head.getWorldPosition(new THREE.Vector3()).y : box.max.y - 0.25;
  return {
    top: box.max.y + 0.05,
    bottom: headY - 0.5,
    width: Math.max(box.max.x - box.min.x, 0.5) + 0.1,
  };
}

export function fitCamera(framing, fovDegrees, aspect) {
  const tanHalf = Math.tan(THREE.MathUtils.degToRad(fovDegrees / 2));
  const forHeight = (framing.top - framing.bottom) / 2 / tanHalf;
  const forWidth = framing.width / 2 / (tanHalf * aspect);
  return { y: (framing.top + framing.bottom) / 2, dist: Math.max(forHeight, forWidth) };
}

export class AvatarController {
  constructor(vrm, lookTarget = null) {
    this.vrm = vrm;
    this.expr = vrm.expressionManager;
    this.t = 0;

    this.mood = null;
    this.moodName = null;
    this.tilt = 0;
    this.dip = 0;
    this.moodWeight = 0;
    this.moodHold = 0;
    this.emotionValues = Object.fromEntries(EMOTIONS.map((e) => [e, 0]));

    this.talkTimer = 0;
    this.mouthTimer = 0;
    this.mouthTarget = {};
    this.mouthValues = Object.fromEntries(VOWELS.map((v) => [v, 0]));

    this.emotionNames = {};
    for (const e of EMOTIONS) {
      const options = NAME_CANDIDATES[e] || [e];
      this.emotionNames[e] = options.find((n) => this.expr && this.expr.getExpression(n)) || null;
    }

    this.blinkTimer = rand(1.5, 4);
    this.blinkPhase = -1;

    this.bones = {};
    for (const name of BONES) {
      this.bones[name] = vrm.humanoid ? vrm.humanoid.getNormalizedBoneNode(name) : null;
    }
    if (lookTarget && vrm.lookAt) vrm.lookAt.target = lookTarget;
  }

  get isTalking() {
    return this.talkTimer > 0;
  }

  _set(name, value) {
    if (this.expr && this.expr.getExpression(name)) this.expr.setValue(name, value);
  }

  setMood(name, hold = 4) {
    const m = MOODS[name];
    if (!m) return;
    [this.mood, this.moodWeight] = m;
    this.moodName = name;
    this.moodHold = hold;
  }

  talkFor(seconds) {
    this.talkTimer = Math.max(this.talkTimer, seconds);
  }

  stopTalking() {
    this.talkTimer = 0;
  }

  update(dtRaw) {
    const dt = Math.min(Math.max(dtRaw, 0), 0.1); 
    this.t += dt;
    const t = this.t;

    if (this.moodHold > 0) this.moodHold -= dt;
    for (const e of EMOTIONS) {
      const target = this.mood === e && this.moodHold > 0 ? this.moodWeight : 0;
      this.emotionValues[e] = approach(this.emotionValues[e], target, 6, dt);
      if (this.emotionNames[e]) this._set(this.emotionNames[e], this.emotionValues[e]);
    }

    const talking = this.talkTimer > 0;
    if (talking) this.talkTimer -= dt;
    this.mouthTimer -= dt;
    if (this.mouthTimer <= 0) {
      this.mouthTimer = rand(0.08, 0.16);
      this.mouthTarget = {};
      if (talking && Math.random() > 0.15) {
        this.mouthTarget[VOWELS[Math.floor(Math.random() * VOWELS.length)]] = rand(0.3, 0.9);
      }
    }
    for (const v of VOWELS) {
      const target = talking ? this.mouthTarget[v] || 0 : 0;
      this.mouthValues[v] = approach(this.mouthValues[v], target, 22, dt);
      this._set(v, this.mouthValues[v]);
    }

    if (this.blinkPhase >= 0) {
      this.blinkPhase += dt;
      const duration = 0.18;
      const p = this.blinkPhase / duration;
      let value = p < 0.4 ? p / 0.4 : Math.max(0, 1 - (p - 0.4) / 0.6);
      if (this.blinkPhase >= duration) {
        this.blinkPhase = -1;
        this.blinkTimer = rand(2, 5.5);
        value = 0;
      }
      this._set('blink', value);
    } else {
      this.blinkTimer -= dt;
      if (this.blinkTimer <= 0) this.blinkPhase = 0;
    }

    const active = this.moodHold > 0 ? this.moodName : null;
    this.tilt = approach(this.tilt, active === 'confused' ? 0.16 : 0, 4, dt);
    this.dip = approach(this.dip, active === 'fallback' || active === 'error' ? 0.1 : 0, 4, dt);

    const b = this.bones;
    const breathe = Math.sin(t * 1.7);
    if (b.spine) b.spine.rotation.x = breathe * 0.01;
    if (b.chest) b.chest.rotation.x = breathe * 0.015;
    if (b.leftUpperArm) b.leftUpperArm.rotation.z = ARM_ANGLE + breathe * 0.015;
    if (b.rightUpperArm) b.rightUpperArm.rotation.z = -ARM_ANGLE - breathe * 0.015;
    if (b.neck) b.neck.rotation.y = Math.sin(t * 0.5) * 0.04;
    if (b.head) {
      b.head.rotation.x = Math.sin(t * 0.7) * 0.02 + (talking ? Math.sin(t * 7) * 0.02 : 0) - this.dip; 
      b.head.rotation.y = Math.sin(t * 0.45 + 1) * 0.05;
      b.head.rotation.z = Math.sin(t * 0.33) * 0.015 + this.tilt;
    }

    this.vrm.update(dt); 
  }
}
