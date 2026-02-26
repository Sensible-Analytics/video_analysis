import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Points, PointMaterial, Stars, OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

const Helix = ({ count = 200, radius = 5, color = "#FFD700", offset = 0, speed = 0.5 }) => {
  const points = useRef();
  
  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    const angle = (i / count) * Math.PI * 10;
    const x = Math.cos(angle + offset) * radius;
    const y = (i / count) * 15 - 7.5;
    const z = Math.sin(angle + offset) * radius;
    positions.set([x, y, z], i * 3);
  }

  useFrame((state) => {
    points.current.rotation.y += speed * 0.01;
  });

  return (
    <Points ref={points} positions={positions} stride={3}>
      <PointMaterial
        transparent
        color={color}
        size={0.15}
        sizeAttenuation={true}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </Points>
  );
};

export default function SplitHelixVisualization() {
  return (
    <div style={{ width: '100%', height: '100vh', background: '#050505' }}>
      <Canvas camera={{ position: [0, 0, 20], fov: 45 }}>
        <color attach="background" args={['#050505']} />
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        
        <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
        
        {/* Manifest Strand (Gold/Light) */}
        <Helix count={300} radius={4} color="#FFD700" speed={0.4} />
        
        {/* Unmanifest Strand (Blue/Electric) */}
        <Helix count={300} radius={4} color="#00E5FF" offset={Math.PI} speed={0.4} />
        
        <OrbitControls enableZoom={false} enablePan={false} />
      </Canvas>
      <div style={{
        position: 'absolute',
        top: '10%',
        left: '5%',
        color: 'white',
        fontFamily: 'Helvetica, Arial, sans-serif'
      }}>
        <h1 style={{ fontSize: '3rem', margin: 0, color: '#FFD700' }}>Mandukya AI</h1>
        <p style={{ fontStyle: 'italic', opacity: 0.7 }}>The Split-Helix Perspective</p>
      </div>
    </div>
  );
}
