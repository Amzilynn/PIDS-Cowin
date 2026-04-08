# 3D Avatar Shareable Assets

This folder contains the assembled 3D MetaHuman avatar, optimized for web integration (React, Three.js, etc.).

## 📦 Files
- `Main.glb`: Static version of the character with **Hair and Eyebrows** fully attached. Best for static previews.
- `Main_Animated.glb`: Animated version containing the **MetaHuman Performance (Talking Animation)**. 
- `README.md`: This instruction file.

## 🚀 How to use in React (React Three Fiber)

1. **Upload the file** to your `public/` folder.
2. **Load the model** using `@react-three/drei`:

```javascript
import { useGLTF, useAnimations } from '@react-three/drei'

function Avatar() {
  const { scene, animations } = useGLTF('/shared/Main_Animated.glb')
  const { actions } = useAnimations(animations, scene)

  useEffect(() => {
    // Play the talking animation
    if (actions) {
      const action = actions[Object.keys(actions)[0]] // Loads the first animation track
      action.play()
    }
  }, [actions])

  return <primitive object={scene} />
}
```

## 🛠️ Technical Notes for Developers
- **Hair Rendering:** The hair uses "Mesh Cards." To prevent transparency issues, ensure the material is set to `doubleSided` in your Three.js engine.
- **Animations:** The `Main_Animated.glb` contains the baked skeleton animation from the MetaHuman Performance capture.
- **Performance:** These models are high-detail. It is recommended to use `Suspense` and potentially compressed textures if loading times are an issue on mobile.

---
*Assembled and exported automatically via Antigravity AI Engine.*
