import React, { useRef, Suspense, useEffect } from 'react';
import { useGLTF, useTexture, Environment } from '@react-three/drei';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';

function ActualMetaHuman({ isSpeaking, speechPulse = 0, ...props }) {
  const rotationGroup = useRef();
  const positionGroup = useRef();
  const { camera } = useThree();
  
  const { scene } = useGLTF('/assets/avatar/ava.glb', 'https://www.gstatic.com/draco/versioned/decoders/1.5.5/');
  
  // Load external textures
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
    // Configure textures
    baseColor.flipY = false;
    baseColor.colorSpace = THREE.SRGBColorSpace;
    baseColor.needsUpdate = true;
    
    normalMap.flipY = false;
    normalMap.needsUpdate = true;
    
    scene.traverse(node => {
      if (node.isMesh && node.material) {
        node.castShadow = true;
        node.receiveShadow = true;
        
        // The GLB material names are often empty strings.
        // We only apply the external skin textures to the body and face meshes that lack natives maps.
        const hasNativeMap = !!node.material.map;
        const isBody = node.name === 'Body001';
        const isFace = node.name.startsWith('Face');
        
        if (!hasNativeMap && (isBody || isFace)) {
          if (isBody) {
             // Create a "bodysuit" by overriding the naked body mesh with a solid color.
             // This also fixes the red UV artifacts that happened when applying the face texture to the body!
             node.material = new THREE.MeshStandardMaterial({
                 color: new THREE.Color('#0f2b3c'), // Dark clinical blue
                 roughness: 0.7,
                 metalness: 0.1,
                 envMapIntensity: 0.5
             });
          } else {
             // Face gets the realistic skin textures
             node.material = node.material.clone();
             node.material.map = baseColor;
             node.material.normalMap = normalMap;
             node.material.normalScale = new THREE.Vector2(1, 1);
             node.material.color = new THREE.Color(0xffffff); 
             node.material.roughness = 0.55;
             node.material.metalness = 0.0;
             node.material.envMapIntensity = 1.0;
          }
          node.material.needsUpdate = true;
        }  
        // If it has a native map (like the Eyes), we literally do NOT touch it. 
        // We let the native glTF loader and the GLB's internal settings handle it!
      }
    });

    // Center face/upper body at origin so OrbitControls frames it correctly
    const box = new THREE.Box3().setFromObject(scene);
    const center = new THREE.Vector3();
    const size = new THREE.Vector3();
    box.getCenter(center);
    box.getSize(size);

    if (positionGroup.current) {
      // 82% from bottom of model is approximately the face/chest area
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
       <Environment preset="studio" />
       <ActualMetaHuman {...props} />
    </Suspense>
  );
}

useGLTF.preload('/assets/avatar/ava.glb');
