"use client";

import { useEffect, useRef, useState } from "react";

interface Particle {
    x: number;
    y: number;
    vx: number;
    vy: number;
    radius: number;
    opacity: number;
    maxConnections: number;
}

export default function ParticleBackground() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [isMobile, setIsMobile] = useState(false);

    useEffect(() => {
        const checkMobile = () => window.innerWidth < 768;
        setIsMobile(checkMobile());

        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        let animationId: number;
        let particles: Particle[] = [];

        // Particle settings - visible dots with sparse connections
        const getParticleCount = () => (window.innerWidth < 768 ? 18 : 35);
        const connectionDistance = 80; // Short range for sparse connections
        const particleColor = "148, 163, 184"; // Slate-400

        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            setIsMobile(window.innerWidth < 768);
        };

        const createParticles = () => {
            particles = [];
            const count = getParticleCount();
            for (let i = 0; i < count; i++) {
                particles.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    // Slow, natural movement
                    vx: (Math.random() - 0.5) * 0.12,
                    vy: (Math.random() - 0.5) * 0.12,
                    // Small but visible dots
                    radius: Math.random() * 1.2 + 0.8, // 0.8 - 2.0px
                    // Clearly visible opacity
                    opacity: Math.random() * 0.06 + 0.12, // 0.12 - 0.18
                    // Limit connections per dot
                    maxConnections: Math.floor(Math.random() * 2) + 1, // 1-2 max
                });
            }
        };

        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Track connections per particle
            const connectionCount: number[] = new Array(particles.length).fill(0);

            // First pass: Draw sparse connections
            particles.forEach((particle, i) => {
                if (connectionCount[i] >= particle.maxConnections) return;

                for (let j = i + 1; j < particles.length; j++) {
                    if (connectionCount[i] >= particle.maxConnections) break;
                    if (connectionCount[j] >= particles[j].maxConnections) continue;

                    const dx = particles[j].x - particle.x;
                    const dy = particles[j].y - particle.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    if (distance < connectionDistance) {
                        // Smooth fade based on distance
                        const opacity = (1 - distance / connectionDistance) * 0.06; // 0.04-0.06

                        ctx.beginPath();
                        ctx.moveTo(particle.x, particle.y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.strokeStyle = `rgba(${particleColor}, ${opacity})`;
                        ctx.lineWidth = 0.6;
                        ctx.stroke();

                        connectionCount[i]++;
                        connectionCount[j]++;
                    }
                }
            });

            // Second pass: Draw dots (on top of lines)
            particles.forEach((particle) => {
                // Update position
                particle.x += particle.vx;
                particle.y += particle.vy;

                // Wrap around edges
                if (particle.x < 0) particle.x = canvas.width;
                if (particle.x > canvas.width) particle.x = 0;
                if (particle.y < 0) particle.y = canvas.height;
                if (particle.y > canvas.height) particle.y = 0;

                // Draw dot with soft glow effect
                // Outer glow
                const gradient = ctx.createRadialGradient(
                    particle.x, particle.y, 0,
                    particle.x, particle.y, particle.radius * 2.5
                );
                gradient.addColorStop(0, `rgba(${particleColor}, ${particle.opacity})`);
                gradient.addColorStop(0.4, `rgba(${particleColor}, ${particle.opacity * 0.5})`);
                gradient.addColorStop(1, `rgba(${particleColor}, 0)`);

                ctx.beginPath();
                ctx.arc(particle.x, particle.y, particle.radius * 2.5, 0, Math.PI * 2);
                ctx.fillStyle = gradient;
                ctx.fill();

                // Core dot
                ctx.beginPath();
                ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(${particleColor}, ${particle.opacity * 1.2})`;
                ctx.fill();
            });

            animationId = requestAnimationFrame(animate);
        };

        resize();
        createParticles();
        animate();

        const handleResize = () => {
            resize();
            createParticles();
        };

        window.addEventListener("resize", handleResize);

        return () => {
            cancelAnimationFrame(animationId);
            window.removeEventListener("resize", handleResize);
        };
    }, [isMobile]);

    return (
        <canvas
            ref={canvasRef}
            className="fixed inset-0 pointer-events-none z-0 opacity-40"
            style={{ background: "transparent" }}
            aria-hidden="true"
        />
    );
}

