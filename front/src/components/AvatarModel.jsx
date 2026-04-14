import React, { useRef, Suspense, useMemo, useEffect, useState } from 'react';
import { useGLTF } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

function applyCustomMaterials(scene) {
  if (!scene) return;
  
  scene.traverse((node) => {
    if (node.isMesh) {
      node.castShadow = true;
      node.receiveShadow = true;
      node.frustumCulled = false;
      
      const name = node.name?.toLowerCase() || '';
      if (name.includes('sky') || name.includes('floor') || name.includes('bound') || name.includes('box')) {
        node.visible = false;
        return;
      }
      
      if (node.material) {
        const materials = Array.isArray(node.material) ? node.material : [node.material];
        
        materials.forEach(mat => {
          let targetColor = 0xb4a9a0; 
          
          const isSkin = name.includes('head') || name.includes('face') || name.includes('skin') || 
                         name.includes('body') || name.includes('arm') || name.includes('leg') ||
                         name.includes('hand') || name.includes('m_med') || name.includes('lod');

          const isHair = name.includes('hair') || name.includes('brow') || name.includes('lash') || 
                         name.includes('mustache') || name.includes('beard');

          const isEye = name.includes('eye') || name.includes('cornea') || name.includes('iris');

          if (isSkin) {
            targetColor = 0xac9675; // Warm Olive tone
          } else if (isHair) {
            targetColor = 0x1a110a; // Dark brunette
          } else if (isEye) {
            targetColor = 0x4b3a2a; // Hazel/Dark Amber eyes
          } else if (name.includes('cloth') || name.includes('top') || name.includes('suit') || name.includes('shirt')) {
            targetColor = 0x272b36; // Professional midnight blue
          }

          if (mat.color) {
            mat.color.setHex(targetColor);
            mat.map = null;
            mat.normalMap = null;
            mat.vertexColors = false; 
            mat.roughness = isSkin ? 0.7 : 0.8;
            mat.metalness = 0.0;
            mat.needsUpdate = true;
          }
        });
      }
    }
  });
  console.log('[AvatarModel] Color correction applied');
}

function MetaHumanAvatar({ isSpeaking, speechPulse = 0, ...props }) {
  const group = useRef();
  const meshRef = useRef();
  const [ready, setReady] = useState(false);
  
  const { scene: gltfScene } = useGLTF('/shared/Main.glb');

  useEffect(() => {
    if (!gltfScene) return;
    
    const box = new THREE.Box3().setFromObject(gltfScene);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);
    
    const targetHeight = 1.4;
    const scale = targetHeight / size.y;
    gltfScene.scale.setScalar(scale);
    
    gltfScene.position.x = -center.x * scale;
    gltfScene.position.y = (-center.y * scale) - 0.1; 
    gltfScene.position.z = -center.z * scale;
    
    applyCustomMaterials(gltfScene);
    setReady(true);
  }, [gltfScene]);

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    
    if (group.current) {
      group.current.rotation.y = Math.sin(time * 0.15) * 0.08;
    }
    
    if (!gltfScene) return;
    
    gltfScene.traverse((child) => {
      if (child.isMesh && child.morphTargetInfluences && child.morphTargetDictionary) {
        const jawIdx = child.morphTargetDictionary['jawOpen'] || 
                       child.morphTargetDictionary['MouthOpen'] || 
                       child.morphTargetDictionary['mouthOpen'] ||
                       child.morphTargetDictionary['Jaw_Open'];
        
        if (jawIdx !== undefined) {
          if (isSpeaking) {
            const targetMouth = Math.min(speechPulse * 1.5, 1);
            child.morphTargetInfluences[jawIdx] = THREE.MathUtils.lerp(
              child.morphTargetInfluences[jawIdx], targetMouth, 0.4
            );
          } else {
            child.morphTargetInfluences[jawIdx] = THREE.MathUtils.lerp(
              child.morphTargetInfluences[jawIdx], 0, 0.15
            );
          }
        }
      }
    });
  });

  return (
    <group ref={group}>
      {ready && gltfScene && (
        <primitive 
          ref={meshRef}
          object={gltfScene} 
          dispose={null}
        />
      )}
      {!ready && (
        <mesh position={[0, 0, 0]}>
          <sphereGeometry args={[0.2, 32, 32]} />
          <meshStandardMaterial color="#4E8C8A" wireframe />
        </mesh>
      )}
    </group>
  );
}

function LoadingOrb() {
  const mesh = useRef();
  
  useFrame((state) => {
    if (mesh.current) {
      mesh.current.rotation.y += 0.05;
      mesh.current.position.y = Math.sin(state.clock.getElapsedTime()) * 0.1;
    }
  });

  return (
    <group position={[0, 0, 0]}>
      <ambientLight intensity={1} />
      <mesh ref={mesh}>
        <sphereGeometry args={[0.3, 16, 16]} />
        <meshStandardMaterial color="#4E8C8A" wireframe />
      </mesh>
    </group>
  );
}

export default function AvatarModel({ isSpeaking = false, speechPulse = 0 }) {
  return (
    <Suspense fallback={<LoadingOrb />}>
      <color attach="background" args={['#11111a']} />
      <ambientLight intensity={0.5} color="#ffffff" />
      <hemisphereLight intensity={0.4} color="#b1e1ff" groundColor="#333333" />
      <directionalLight 
        position={[2, 4, 3]} 
        intensity={0.8} 
        castShadow 
      />
      <directionalLight 
        position={[-2, 2, 2]} 
        intensity={0.4} 
        color="#e8f4ff" 
      />
      <spotLight 
        position={[0, 5, 2]} 
        angle={0.5} 
        penumbra={1} 
        intensity={0.7} 
      />
      <pointLight 
        position={[0, 2, 2]} 
        intensity={0.4} 
        color="#ffe4d4" 
      />
      <MetaHumanAvatar 
        isSpeaking={isSpeaking} 
        speechPulse={speechPulse} 
      />
    </Suspense>
  );
}

useGLTF.preload('/shared/Main.glb');
