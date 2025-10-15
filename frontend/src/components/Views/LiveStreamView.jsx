"use client";

import { useEffect, useRef, useState } from "react";
import Hls from "hls.js";

export default function LiveStreamView({ formattedDate, formattedTime }) {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const streamUrl = `${process.env.NEXT_PUBLIC_API_URL}/hls/stream.m3u8`;

    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 30,
        maxBufferLength: 30,
        maxMaxBufferLength: 30,
        liveSyncDurationCount: 2,
        liveMaxLatencyDurationCount: 3,
        maxLiveSyncPlaybackRate: 1.5,
      });

      hlsRef.current = hls;

      hls.loadSource(streamUrl);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        console.log("✓ HLS stream loaded successfully");
        setIsLoading(false);

        // Auto-play with muted audio
        video.muted = true;
        video
          .play()
          .then(() => console.log("✓ Video playing"))
          .catch((err) => {
            console.error("Autoplay failed:", err);
            setError("Click to play the stream");
          });
      });

      hls.on(Hls.Events.ERROR, (event, data) => {
        console.error("HLS Error:", data);

        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              console.log("Network error, retrying...");
              setTimeout(() => hls.startLoad(), 1000);
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              console.log("Media error, recovering...");
              hls.recoverMediaError();
              break;
            default:
              setError(
                "Stream unavailable. Please check if FFmpeg is running."
              );
              hls.destroy();
              break;
          }
        }
      });

      return () => {
        if (hlsRef.current) {
          hlsRef.current.destroy();
        }
      };
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      // Native HLS support (Safari)
      video.src = streamUrl;
      video.muted = true;
      video.addEventListener("loadedmetadata", () => {
        setIsLoading(false);
        video.play().catch((err) => {
          console.error("Autoplay failed:", err);
          setError("Click to play the stream");
        });
      });
    } else {
      setError("HLS is not supported in this browser");
    }
  }, []);

  // Click to play if autoplay fails
  const handleClick = () => {
    if (videoRef.current && videoRef.current.paused) {
      videoRef.current.muted = true;
      videoRef.current.play();
      setError(null);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-gray-100 px-6 pt-6 flex justify-between items-start">
        <h1 className="text-4xl font-semibold text-gray-900">
          Real Time Monitoring
        </h1>
        <div className="text-right">
          <div className="text-gray-700 text-md font-medium">
            {formattedDate}
          </div>
          <div className="text-gray-500 text-sm">{formattedTime}</div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 bg-gray-100 md:px-12 p-6 pt-4">
        <div
          className="bg-black rounded-lg overflow-hidden shadow relative cursor-pointer"
          onClick={handleClick}
        >
          {/* Loading Overlay */}
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-900 z-10">
              <div className="text-center">
                <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500 mb-4"></div>
                <p className="text-white">Loading stream...</p>
              </div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-900 z-10">
              <div className="text-center text-red-500">
                <svg
                  className="w-16 h-16 mx-auto mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p className="text-lg font-semibold mb-2">{error}</p>
                <p className="text-sm text-gray-400">Click to play</p>
              </div>
            </div>
          )}

          {/* Video Player - NO CONTROLS */}
          <video
            ref={videoRef}
            className="w-full h-auto"
            style={{ maxHeight: "80vh" }}
            autoPlay
            muted
            playsInline
            loop={false}
          />

          {/* Stream Status Indicator */}
          {!isLoading && !error && (
            <div className="absolute top-4 right-4 flex items-center space-x-2 bg-black bg-opacity-60 px-3 py-2 rounded-lg">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
              <span className="text-white text-sm font-medium">LIVE</span>
            </div>
          )}

          {/* Muted Indicator */}
          {!isLoading && !error && (
            <div className="absolute bottom-4 left-4 flex items-center space-x-2 bg-black bg-opacity-60 px-3 py-2 rounded-lg">
              <svg
                className="w-5 h-5 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"
                />
              </svg>
              <span className="text-white text-sm">Muted</span>
            </div>
          )}
        </div>

        {/* Stream Info Cards */}
        <div className="mt-4 grid grid-cols-3 gap-4">
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm">Status</p>
            <p className="text-white font-semibold">
              {isLoading ? "Loading..." : error ? "Error" : "Live"}
            </p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm">Protocol</p>
            <p className="text-white font-semibold">HLS</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm">Latency</p>
            <p className="text-white font-semibold">~4-6s</p>
          </div>
        </div>
      </div>
    </div>
  );
}
