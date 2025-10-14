"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import styles from "./loader.module.css";

gsap.registerPlugin(useGSAP);

export default function Loader({ isConnected, onAnimationComplete }) {
  const containerRef = useRef(null);
  const grayLayerRef = useRef(null);
  const textRef = useRef(null);
  const timelineRef = useRef(null);
  const isFirstLoadRef = useRef(true);

  useGSAP(
    () => {
      // Kill any existing timeline
      if (timelineRef.current) {
        timelineRef.current.kill();
      }

      const tl = gsap.timeline({ paused: true });

      if (isFirstLoadRef.current) {
        // FIRST LOAD SEQUENCE

        // 1. Show gray background for 1 second
        tl.to({}, { duration: 1 });

        // 2. Bars slide in from left
        tl.fromTo(
          `.${styles.bar}`,
          {
            clipPath: "polygon(0% 0%, 0% 0%, 0% 100%, 0% 100%)",
          },
          {
            clipPath: "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)",
            duration: 1,
            ease: "power4.inOut",
            stagger: {
              amount: 0.5,
              from: "random",
            },
          }
        );

        // 3. Finder images scale up
        tl.to(`.${styles.finderContainer} img`, {
          scale: 1,
          delay: 0.5,
        });

        // 4. "SENTINEL" text fades in
        tl.to(
          textRef.current,
          {
            opacity: 1,
            duration: 0.75,
            ease: "power2.in",
          },
          "<"
        );

        // 5. Marquee scroll in
        tl.to(`.${styles.marquee}`, {
          left: "0vw",
          duration: 4,
          ease: "power4.inOut",
          onComplete: () => {
            gsap.to(`.${styles.marquee}`, {
              opacity: 0,
              repeat: 4,
              yoyo: true,
              duration: 0.1,
              onComplete: () => {
                gsap.to(`.${styles.marquee}`, {
                  opacity: 1,
                });
              },
            });
          },
        });

        // 6. Pause for 2 seconds regardless of connection
        tl.to({}, { duration: 2 });

        // PAUSE POINT - wait here until WebSocket connects
        tl.addLabel("waitForConnection");

        // 7. Fade out gray background (revealing content behind)
        tl.to(grayLayerRef.current, {
          opacity: 0,
          duration: 0.5,
        });

        // 8. Pause for 2 seconds
        tl.to({}, { duration: 2 });

        // 9. Flicker effect on text while frames scale out
        tl.to(textRef.current, {
          opacity: 0,
          repeat: 8,
          yoyo: true,
          duration: 0.08,
          ease: "none",
        });

        // 10. Outro - Finder images scale out (happens with flicker)
        tl.to(
          `.${styles.finderContainer} img`,
          {
            scale: 0,
            duration: 0.5,
            stagger: 0.075,
          },
          "<"
        );

        // 11. Marquee scroll out
        tl.to(
          `.${styles.marquee}`,
          {
            left: "-100vw",
            duration: 4,
            ease: "power4.inOut",
          },
          "<"
        );

        // 12. Bars slide out to the right (revealing content underneath)
        tl.to(
          `.${styles.bar}`,
          {
            clipPath: "polygon(100% 0%, 100% 0%, 100% 100%, 100% 100%)",
            duration: 1,
            ease: "power4.inOut",
            stagger: {
              amount: 0.5,
              from: "random",
            },
          },
          "-=2"
        );

        // 13. Fade out entire container
        tl.to(containerRef.current, {
          opacity: 0,
          duration: 0.5,
          onComplete: () => {
            if (onAnimationComplete) onAnimationComplete();
            isFirstLoadRef.current = false;
          },
        });
      } else {
        // SUBSEQUENT LOADS (after reconnection)

        // 1. Fade in gray background with delay
        tl.to(grayLayerRef.current, {
          opacity: 1,
          duration: 0.5,
          delay: 0.5,
        });

        // 2. Bars slide in
        tl.fromTo(
          `.${styles.bar}`,
          {
            clipPath: "polygon(0% 0%, 0% 0%, 0% 100%, 0% 100%)",
          },
          {
            clipPath: "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)",
            duration: 1,
            ease: "power4.inOut",
            stagger: {
              amount: 0.5,
              from: "random",
            },
          }
        );

        // 3. Finder images scale up
        tl.to(`.${styles.finderContainer} img`, {
          scale: 1,
          delay: 0.5,
        });

        // 4. Text fades in
        tl.to(
          textRef.current,
          {
            opacity: 1,
            duration: 0.75,
            ease: "power2.in",
          },
          "<"
        );

        // 5. Marquee scroll in
        tl.to(`.${styles.marquee}`, {
          left: "0vw",
          duration: 4,
          ease: "power4.inOut",
          onComplete: () => {
            gsap.to(`.${styles.marquee}`, {
              opacity: 0,
              repeat: 4,
              yoyo: true,
              duration: 0.1,
              onComplete: () => {
                gsap.to(`.${styles.marquee}`, {
                  opacity: 1,
                });
              },
            });
          },
        });

        // PAUSE POINT - wait here until WebSocket connects
        tl.addLabel("waitForConnection");

        // 6. Fade out gray background
        tl.to(grayLayerRef.current, {
          opacity: 0,
          duration: 0.5,
        });

        // 7. Pause for 2 seconds
        tl.to({}, { duration: 2 });

        // 8. Flicker effect on text
        tl.to(textRef.current, {
          opacity: 0,
          repeat: 8,
          yoyo: true,
          duration: 0.08,
          ease: "none",
        });

        // 9. Outro animations
        tl.to(
          `.${styles.finderContainer} img`,
          {
            scale: 0,
            duration: 0.5,
            stagger: 0.075,
          },
          "<"
        );

        tl.to(
          `.${styles.marquee}`,
          {
            left: "-100vw",
            duration: 4,
            ease: "power4.inOut",
          },
          "<"
        );

        tl.to(
          `.${styles.bar}`,
          {
            clipPath: "polygon(100% 0%, 100% 0%, 100% 100%, 100% 100%)",
            duration: 1,
            ease: "power4.inOut",
            stagger: {
              amount: 0.5,
              from: "random",
            },
          },
          "-=2"
        );

        tl.to(containerRef.current, {
          opacity: 0,
          duration: 0.5,
          onComplete: () => {
            if (onAnimationComplete) onAnimationComplete();
          },
        });
      }

      timelineRef.current = tl;

      // Start playing from the beginning
      tl.restart();

      // Pause at the waiting point
      tl.pause("waitForConnection");
    },
    { scope: containerRef, dependencies: [isConnected], revertOnUpdate: false }
  );

  // Resume animation when WebSocket connects
  useEffect(() => {
    if (isConnected && timelineRef.current) {
      timelineRef.current.play();
    }
  }, [isConnected]);

  return (
    <div ref={containerRef} className={styles.container}>
      {/* Gray background layer */}
      <div ref={grayLayerRef} className={styles.grayLayer}></div>

      {/* Loader with bars */}
      <div className={styles.loader}>
        <div className={styles.finderContainer}>
          <img src="/images/frame.png" alt="" />
          <img src="/images/frame.png" alt="" />
          <img src="/images/frame.png" alt="" />
          <img src="/images/frame.png" alt="" />
          <img src="/images/frame.png" alt="" />

          {/* SENTINEL text overlay */}
          <div ref={textRef} className={styles.sentinelText}>
            SENTINEL
          </div>
        </div>

        <div className={`${styles.bar} ${styles.bar1}`}>
          <div className={styles.marquee}>
            {Array(20)
              .fill(0)
              .map((_, i) => (
                <p key={`marquee-1-${i}`}>
                  <span>■</span>Sentinel
                </p>
              ))}
          </div>
        </div>
        <div className={`${styles.bar} ${styles.bar2}`}></div>
        <div className={`${styles.bar} ${styles.bar3}`}></div>
        <div className={`${styles.bar} ${styles.bar4}`}></div>
        <div className={`${styles.bar} ${styles.bar5}`}>
          <div className={styles.marquee}>
            {Array(20)
              .fill(0)
              .map((_, i) => (
                <p key={`marquee-5-${i}`}>
                  <span>■</span>Sentinel
                </p>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}
