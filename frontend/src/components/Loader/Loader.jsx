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

  useGSAP(
    () => {
      const tl = gsap.timeline();

      // 1. Gray background visible for 0.5 seconds
      tl.to({}, { duration: 0.5 });

      // 2. Bars slide in
      tl.fromTo(
        `.${styles.bar}`,
        { clipPath: "polygon(0% 0%, 0% 0%, 0% 100%, 0% 100%)" },
        {
          clipPath: "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)",
          duration: 1,
          ease: "power4.inOut",
          stagger: { amount: 0.5, from: "random" },
        }
      );

      // 3. Images scale up
      tl.to(
        `.${styles.finderContainer} img`,
        { scale: 1, duration: 0.5 },
        "-=0.5"
      );

      // 4. Text fades in (at same time as images)
      tl.to(
        textRef.current,
        { opacity: 1, duration: 0.75, ease: "power2.in" },
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
            onComplete: () => gsap.to(`.${styles.marquee}`, { opacity: 1 }),
          });
        },
      });

      // 6. PAUSE HERE AFTER INTRO - wait for WebSocket connection
      tl.addLabel("waitForConnection");
      tl.call(() => {
        // Only pause if not connected yet
        if (!isConnected) {
          tl.pause();
        }
      });

      // 7. Once connected, pause for 2 seconds
      tl.to({}, { duration: 2 });

      // 8. Gray layer fade out (revealing content underneath)
      tl.to(grayLayerRef.current, { opacity: 0, duration: 0.5 });

      // 9. Text flicker while images scale out
      tl.to(textRef.current, {
        opacity: 0,
        repeat: 8,
        yoyo: true,
        duration: 0.08,
        ease: "none",
      });

      // 10. Images scale out (happens with flicker)
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

      // 12. Bars slide out to the right
      tl.to(
        `.${styles.bar}`,
        {
          clipPath: "polygon(100% 0%, 100% 0%, 100% 100%, 100% 100%)",
          duration: 1,
          ease: "power4.inOut",
          stagger: { amount: 0.5, from: "random" },
        },
        "-=2"
      );

      // 13. Fade out entire container
      tl.to(containerRef.current, {
        opacity: 0,
        duration: 0.5,
        onComplete: () => onAnimationComplete?.(),
      });

      timelineRef.current = tl;
    },
    { scope: containerRef }
  );

  useEffect(() => {
    if (isConnected && timelineRef.current) {
      timelineRef.current.play();
    }
  }, [isConnected]);

  return (
    <div ref={containerRef} className={styles.container}>
      <div ref={grayLayerRef} className={styles.grayLayer}></div>
      <div className={styles.loader}>
        <div className={styles.finderContainer}>
          <img src="/images/frame.png" alt="" />
          <img src="/images/frame.png" alt="" />
          <img src="/images/frame.png" alt="" />
          <img src="/images/frame.png" alt="" />
          <img src="/images/frame.png" alt="" />
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
