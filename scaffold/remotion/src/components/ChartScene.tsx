import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface ChartSceneProps {
  text: string;
  chartType: string;
  durationInFrames: number;
}

export const ChartScene: React.FC<ChartSceneProps> = ({
  text,
  chartType,
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
          DATA
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
          transform: "translate(-50%, -45%)",
          width: 860,
          height: 450,
        }}
      >
        {chartType === "skill_compounding" && (
          <SkillCompoundingChart frame={frame} durationInFrames={durationInFrames} />
        )}
      </div>
    </AbsoluteFill>
  );
};

const SkillCompoundingChart: React.FC<{ frame: number; durationInFrames: number }> = ({
  frame,
  durationInFrames,
}) => {
  const chartLeft = 90;
  const chartRight = 780;
  const chartTop = 40;
  const chartBottom = 360;
  const chartWidth = chartRight - chartLeft;
  const chartHeight = chartBottom - chartTop;

  const draw = interpolate(frame, [10, durationInFrames - 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  const tasks = [1, 2, 3, 4, 5, 6, 7, 8];
  const noSkill = [0.18, 0.2, 0.22, 0.25, 0.29, 0.32, 0.34, 0.36];
  const withSkill = [0.18, 0.24, 0.32, 0.44, 0.58, 0.72, 0.84, 0.93];

  const toPoint = (index: number, v: number) => {
    const x = chartLeft + (index / (tasks.length - 1)) * chartWidth;
    const y = chartBottom - v * chartHeight * draw;
    return { x, y };
  };

  const pointsNoSkill = noSkill.map((v, i) => toPoint(i, v));
  const pointsWithSkill = withSkill.map((v, i) => toPoint(i, v));

  const buildPath = (points: Array<{ x: number; y: number }>) => {
    return points.reduce((acc, p, i) => {
      if (i === 0) return `M ${p.x} ${p.y}`;
      const prev = points[i - 1];
      const cpx = (prev.x + p.x) / 2;
      return `${acc} C ${cpx} ${prev.y}, ${cpx} ${p.y}, ${p.x} ${p.y}`;
    }, "");
  };

  return (
    <svg viewBox="0 0 860 450" style={{ width: "100%", height: "100%" }}>
      <line x1={chartLeft} y1={chartBottom} x2={chartRight} y2={chartBottom} stroke="rgba(255,255,255,0.3)" />
      <line x1={chartLeft} y1={chartTop} x2={chartLeft} y2={chartBottom} stroke="rgba(255,255,255,0.3)" />

      <path d={buildPath(pointsNoSkill)} fill="none" stroke="#adb5bd" strokeWidth="2.5" strokeDasharray="7 6" />
      <path d={buildPath(pointsWithSkill)} fill="none" stroke="#06d6a0" strokeWidth="3" />

      {pointsWithSkill.map((p, i) => {
        const dot = interpolate(frame, [18 + i * 6, 30 + i * 6], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        return (
          <g key={`with-${i}`} opacity={dot}>
            <circle cx={p.x} cy={p.y} r="10" fill="#06d6a0" opacity="0.2" />
            <circle cx={p.x} cy={p.y} r="4.5" fill="#06d6a0" />
          </g>
        );
      })}

      {pointsNoSkill.map((p, i) => {
        const dot = interpolate(frame, [20 + i * 6, 32 + i * 6], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        return (
          <g key={`without-${i}`} opacity={dot}>
            <circle cx={p.x} cy={p.y} r="4" fill="#adb5bd" />
          </g>
        );
      })}

      <rect x="540" y="64" width="250" height="82" rx="12" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.12)" />
      <line x1="560" y1="91" x2="610" y2="91" stroke="#06d6a0" strokeWidth="3" />
      <text x="620" y="96" fill="#ffffff" fontSize="16" fontFamily="Noto Sans SC, sans-serif">With Skill</text>
      <line x1="560" y1="120" x2="610" y2="120" stroke="#adb5bd" strokeWidth="2.5" strokeDasharray="6 5" />
      <text x="620" y="125" fill="#ffffff" fontSize="16" fontFamily="Noto Sans SC, sans-serif">Without Skill</text>
    </svg>
  );
};
