// frontend/components/StarkSculptor.tsx
'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { FilesetResolver, HandLandmarker } from '@mediapipe/tasks-vision';

export default function StarkSculptor() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [gestureState, setGestureState] = useState<string>('SEARCHING FOR HANDS...');

  useEffect(() => {
    let scene: THREE.Scene, camera: THREE.PerspectiveCamera, renderer: THREE.WebGLRenderer;
    let mesh: THREE.Mesh;
    let handLandmarker: HandLandmarker;

    async function init() {
      // 1. Setup Three.js 3D Holographic Scene
      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
      camera.position.z = 5;

      renderer = new THREE.WebGLRenderer({ canvas: canvasRef.current!, alpha: true, antialias: true });
      renderer.setSize(window.innerWidth, window.innerHeight);

      // Spawn Stark Arc Reactor Core Geometry
      const geometry = new THREE.IcosahedronGeometry(1.5, 2);
      const material = new THREE.MeshBasicMaterial({
        color: 0x00f0ff,
        wireframe: true,
        transparent: true,
        opacity: 0.8,
      });
      mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);

      // 2. Initialize MediaPipe Hand Detector
      const vision = await FilesetResolver.forVisionTasks(
        'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
      );
      handLandmarker = await HandLandmarker.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task',
          delegate: 'GPU',
        },
        runningMode: 'VIDEO',
        numHands: 1,
      });

      // 3. Start Webcam Stream
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play();
        }
      }

      // 4. Real-time Gesture Loop
      function renderLoop() {
        if (videoRef.current && videoRef.current.readyState >= 2) {
          const results = handLandmarker.detectForVideo(videoRef.current, performance.now());

          if (results.landmarks && results.landmarks.length > 0) {
            const landmarks = results.landmarks[0];
            const thumbTip = landmarks[4];
            const indexTip = landmarks[8];

            // Calculate 3D Pinch Distance
            const distance = Math.hypot(
              thumbTip.x - indexTip.x,
              thumbTip.y - indexTip.y,
              thumbTip.z - indexTip.z
            );

            // Gesture 1: Pinch to Scale/Shape Object
            const scale = Math.max(0.5, Math.min(3.0, distance * 10));
            mesh.scale.set(scale, scale, scale);

            // Gesture 2: Move Hand to Rotate Hologram in Space
            mesh.rotation.x = landmarks[9].y * Math.PI * 2;
            mesh.rotation.y = landmarks[9].x * Math.PI * 2;

            setGestureState(distance < 0.08 ? 'PINCH GRAB ACTIVE (SCULPTING)' : 'HAND TRACKED: ROTATING MODEL');
          } else {
            setGestureState('NO HAND DETECTED');
            mesh.rotation.y += 0.01; // Auto-spin when idle
          }
        }

        renderer.render(scene, camera);
        requestAnimationFrame(renderLoop);
      }

      renderLoop();
    }

    init();
  }, []);

  return (
    <div className="relative w-full h-screen overflow-hidden bg-black">
      <video ref={videoRef} className="hidden" playsInline muted />
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full z-0" />
      <div className="absolute top-6 right-6 z-10 bg-[rgba(10,20,35,0.8)] border border-[#00f0ff]/40 p-4 rounded-xl text-xs font-mono text-[#00f0ff]">
        <p className="font-bold tracking-widest uppercase">GESTURE ENGINE // STARK MARK-85</p>
        <p className="text-white mt-1">STATUS: {gestureState}</p>
      </div>
    </div>
  );
}
