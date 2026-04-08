# 3D Avatar Shareable Assets

This folder contains the assembled 3D MetaHuman avatar, optimized for web integration (React, Three.js, etc.).

## 📦 Files
- `Main.glb`: The complete assembled character including:
  - Full body mesh and clothing.
  - High-fidelity face skinning and materials.
  - **Optimized Hair & Eyebrows** (Converted from Unreal Grooms to Mesh Cards).
  - All textures embedded (Self-contained).

## 🚀 How to use in React (React Three Fiber)

1. **Upload the file** to your `public/` folder.
2. **Load the model** using `@react-three/drei`:

```javascript
import { useGLTF } from '@react-three/drei'

function Avatar() {
  const { scene } = useGLTF('/shared/Main.glb')
  return <primitive object={scene} />
}
```

## 🛠️ Technical Notes for Developers
- **Hair Rendering:** The hair uses "Mesh Cards." To prevent transparency issues, ensure the material is set to `doubleSided` in your Three.js engine.
- **Animations:** This version is exported as a high-quality static pose. 
- **Scale:** Exported in standard Unreal units. You may need to scale the primitive down (e.g., `scale={0.01}`) depending on your scene's unit settings.

---
*Assembled and exported automatically via Antigravity AI Engine.*
