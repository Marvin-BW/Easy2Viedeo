import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface AnimationSceneProps {
  text: string;
  animationType: string;
  durationInFrames: number;
}

/**
 * Animation scene component.
 *
 * Custom animations are added per-video by the /science-video skill.
 * Each video generation creates new animation components here, registered
 * in the render block below before the `default` fallback.
 *
 * Pattern for adding a new animation:
 *
 * 1. Define the component:
 *    const MyAnimation: React.FC<{ frame: number; durationInFrames: number }> = ({ frame, durationInFrames }) => {
 *      return <svg viewBox="0 0 920 500">...</svg>;
 *    };
 *
 * 2. Register it in the render block:
 *    {animationType === "my_animation" && (
 *      <MyAnimation frame={frame} durationInFrames={durationInFrames} />
 *    )}
 */
export const AnimationScene: React.FC<AnimationSceneProps> = ({
  text,
  animationType,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleProgress = spring({
    frame,
    fps,
    config: { damping: 15, stiffness: 80 },
  });

  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 15, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ opacity: exitOpacity }}>
      <div
        style={{
          position: "absolute",
          top: 80,
          left: 100,
          opacity: titleProgress,
          transform: `translateX(${interpolate(titleProgress, [0, 1], [-30, 0])}px)`,
        }}
      >
        <div
          style={{
            fontSize: 16,
            color: "rgba(255,255,255,0.5)",
            fontFamily: '"Noto Sans SC", sans-serif',
            letterSpacing: "0.2em",
            marginBottom: 8,
          }}
        >
          SCIENCE
        </div>
        <div
          style={{
            fontSize: 36,
            fontWeight: 600,
            color: "#ffffff",
            fontFamily: '"Noto Sans SC", sans-serif',
          }}
        >
          {text}
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "55%",
          transform: "translate(-50%, -50%)",
          width: 920,
          height: 500,
        }}
      >
        {/* === CUSTOM ANIMATIONS BELOW === */}
        {/* New animations are inserted here by the /science-video skill */}

        {/* === DEFAULT FALLBACK === */}
        {animationType === "default" && <DefaultAnimation text={text} />}
      </div>
    </AbsoluteFill>
  );
};

const DefaultAnimation: React.FC<{ text: string }> = ({ text }) => {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        width: "100%",
        height: "100%",
      }}
    >
      <div
        style={{
          fontSize: 46,
          color: "rgba(255,255,255,0.82)",
          fontFamily: '"Noto Sans SC", sans-serif',
          fontWeight: 500,
          letterSpacing: "0.03em",
        }}
      >
        {text}
      </div>
    </div>
  );
};
