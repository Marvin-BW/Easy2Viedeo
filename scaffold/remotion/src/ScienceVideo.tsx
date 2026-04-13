import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
} from "remotion";
import { TitleScene } from "./components/TitleScene";
import { AnimationScene } from "./components/AnimationScene";
import { ChartScene } from "./components/ChartScene";
import { Subtitle } from "./components/Subtitle";
import { Background } from "./components/Background";

export interface Segment {
  id: string;
  type: "title" | "animation" | "chart";
  text: string;
  narration: string;
  startFrame: number;
  endFrame: number;
  animation?: string;
  chart_type?: string;
}

interface ScienceVideoProps {
  segments?: Segment[];
}

export const ScienceVideo: React.FC<ScienceVideoProps> = ({ segments = [] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill>
      <Background />

      {segments.map((segment) => {
        const duration = segment.endFrame - segment.startFrame;
        return (
          <Sequence
            key={segment.id}
            from={segment.startFrame}
            durationInFrames={duration}
          >
            {segment.type === "title" && (
              <TitleScene text={segment.text} durationInFrames={duration} />
            )}
            {segment.type === "animation" && (
              <AnimationScene
                text={segment.text}
                animationType={segment.animation || "default"}
                durationInFrames={duration}
              />
            )}
            {segment.type === "chart" && (
              <ChartScene
                text={segment.text}
                chartType={segment.chart_type || "bar"}
                durationInFrames={duration}
              />
            )}
          </Sequence>
        );
      })}

      <Subtitle srtFile="subtitles.srt" />
      <Audio src={staticFile("audio.mp3")} />
    </AbsoluteFill>
  );
};
