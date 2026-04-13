import React from "react";
import { Composition, staticFile } from "remotion";
import { ScienceVideo } from "./ScienceVideo";
import scriptData from "./data/script.json";

export const RemotionRoot: React.FC = () => {
  const fps = scriptData.fps || 30;
  const totalDuration = scriptData.totalDurationInFrames || fps * 60;

  return (
    <>
      <Composition
        id="ScienceVideo"
        component={ScienceVideo}
        durationInFrames={totalDuration}
        fps={fps}
        width={1920}
        height={1080}
        defaultProps={{
          segments: scriptData.segments,
        }}
      />
    </>
  );
};
