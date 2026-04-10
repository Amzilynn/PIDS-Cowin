import React, { useRef, Suspense, useEffect } from 'react';
import { useGLTF, useTexture } from '@react-three/drei';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';

function ActualMetaHuman({ isSpeaking, speechPulse = 0, ...props }) {
  const rotationGroup = useRef();
  const positionGroup = useRef();
  const { camera } = useThree();
  
  const { scene } = useGLTF('/assets/avatar/ava.glb', 'https://www.gstatic.com/draco/versioned/decoders/1.5.5/');
  
  const baseColor = useTexture('/assets/avatar/ava_Basecolor.png');
  const normalMap = useTexture('/assets/avatar/ava_Normal.png');

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    // Rotate the outer group so it pivots around the origin perfectly
    if (rotationGroup.current) {
      rotationGroup.current.rotation.y = Math.sin(time * 0.2) * 0.03;
    }

    scene.traverse(child => {
      if (child.isMesh && child.morphTargetInfluences && child.morphTargetDictionary) {
        const jawIdx = child.morphTargetDictionary['jawOpen'] || child.morphTargetDictionary['MouthOpen'] || child.morphTargetDictionary['mouthOpen'];
        if (jawIdx !== undefined) {
          if (isSpeaking) {
            // Explicitly sync to the strict volume curve without falling back to a blind sine-wave during silent pauses
            const targetMouth = speechPulse * 1.5; 
            child.morphTargetInfluences[jawIdx] = THREE.MathUtils.lerp(
               child.morphTargetInfluences[jawIdx], targetMouth, 0.5
            );
          } else {
            child.morphTargetInfluences[jawIdx] = THREE.MathUtils.lerp(child.morphTargetInfluences[jawIdx], 0, 0.1);
          }
        }
      }
    });
  });

  useEffect(() => {
    baseColor.flipY = false;
    baseColor.colorSpace = THREE.SRGBColorSpace;
    baseColor.needsUpdate = true;
    
    normalMap.flipY = false;
    normalMap.needsUpdate = true;
    
    scene.traverse(node => {
      if (node.isMesh) {
        console.log('Mesh found:', node.name);
        node.castShadow = true;
        node.receiveShadow = true;
        
        const nodeName = node.name.toLowerCase();
        
        if (nodeName === 'body001' || nodeName.includes('body')) {
          node.material = new THREE.MeshStandardMaterial({
            color: new THREE.Color('#0f2b3c'),
            roughness: 0.7,
            metalness: 0.1
          });
        }
        else if (nodeName.startsWith('face') || nodeName.includes('face_') || nodeName.includes('skin') || nodeName.includes('head')) {
          node.material = node.material.clone();
          node.material.map = baseColor;
          node.material.normalMap = normalMap;
          node.material.color = new THREE.Color(0xffffff);
          node.material.roughness = 0.55;
          node.material.metalness = 0.0;
        }
        else if (node.material) {
          node.material = new THREE.MeshStandardMaterial({
            color: new THREE.Color('#0f2b3c'),
            roughness: 0.7,
            metalness: 0.1
          });
        }
        if (node.material) node.material.needsUpdate = true;
      }
    });

    const box = new THREE.Box3().setFromObject(scene);
    const center = new THREE.Vector3();
    const size = new THREE.Vector3();
    box.getCenter(center);
    box.getSize(size);

    if (positionGroup.current) {
      const faceY = box.min.y + size.y * 0.82;
      positionGroup.current.position.set(-center.x, -faceY, -center.z);
    }
  }, [scene, baseColor, normalMap]);

  return (
    <group ref={rotationGroup}>
      <group ref={positionGroup}>
        <primitive object={scene} dispose={null} />
      </group>
    </group>
  );
}

function DigitalOrb() {
  const mesh = useRef();
  useFrame((state) => {
    if (mesh.current) {
      mesh.current.rotation.y += 0.005;
      mesh.current.rotation.x = Math.sin(state.clock.getElapsedTime() * 0.3) * 0.1;
    }
  });
  return (
    <group>
      <ambientLight intensity={0.5} />
      <mesh ref={mesh} position={[0, 0, 0]}>
        <sphereGeometry args={[0.3, 24, 24]} />
        <meshStandardMaterial color="#4E8C8A" wireframe transparent opacity={0.6} />
      </mesh>
    </group>
  );
}

export default function AvatarModel(props) {
  return (
    <Suspense fallback={<DigitalOrb />}>
       <ambientLight intensity={0.6} />
       <directionalLight position={[3, 4, 5]} intensity={1.2} castShadow color="#fff5ee" />
       <directionalLight position={[-4, 3, 3]} intensity={0.5} color="#e8f0ff" />
       <directionalLight position={[0, 4, -4]} intensity={0.4} color="#ffffff" />
       <spotLight position={[0, 10, 0]} angle={0.3} penumbra={1} intensity={0.5} castShadow />
       <pointLight position={[-5, 5, 5]} intensity={0.3} color="#e8f0ff" />
       <ActualMetaHuman {...props} />
    </Suspense>
  );
}

useGLTF.preload('/assets/avatar/ava.glb');
