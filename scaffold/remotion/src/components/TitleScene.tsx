import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  spring,
  useVideoConfig,
  Easing,
} from "remotion";

interface TitleSceneProps {
  text: string;
  durationInFrames: number;
}

export const TitleScene: React.FC<TitleSceneProps> = ({
  text,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enterProgress = spring({
    frame,
    fps,
    config: {
      damping: 15,
      stiffness: 80,
      mass: 0.8,
    },
  });

  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 15, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const translateY = interpolate(enterProgress, [0, 1], [60, 0]);
  const opacity = enterProgress * exitOpacity;
  const lineWidth = interpolate(enterProgress, [0, 1], [0, 200]);

  const chars = text.split("");

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        opacity,
      }}
    >
      <div
        style={{
          display: "flex",
          gap: 4,
          transform: `translateY(${translateY}px)`,
        }}
      >
        {chars.map((char, i) => {
          const charDelay = i * 2;
          const charProgress = spring({
            frame: Math.max(0, frame - charDelay),
            fps,
            config: { damping: 12, stiffness: 100, mass: 0.5 },
          });
          const charY = interpolate(charProgress, [0, 1], [30, 0]);
          const charOpacity = charProgress;

          return (
            <span
              key={i}
              style={{
                fontSize: 72,
                fontWeight: 700,
                color: "#ffffff",
                fontFamily:
                  '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
                transform: `translateY(${charY}px)`,
                opacity: charOpacity,
                textShadow: "0 4px 30px rgba(56,97,251,0.3)",
                letterSpacing: "0.05em",
              }}
            >
              {char}
            </span>
          );
        })}
      </div>

      <div
        style={{
          marginTop: 24,
          height: 3,
          width: lineWidth,
          borderRadius: 2,
          background:
            "linear-gradient(90deg, transparent, #3861fb, rgba(139,92,246,0.8), transparent)",
        }}
      />
    </AbsoluteFill>
  );
};
