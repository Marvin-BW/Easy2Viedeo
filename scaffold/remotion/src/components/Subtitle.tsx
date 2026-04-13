import React, { useEffect, useState } from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  staticFile,
  interpolate,
  spring,
} from "remotion";

interface SrtEntry {
  index: number;
  startMs: number;
  endMs: number;
  text: string;
}

function parseSrt(content: string): SrtEntry[] {
  const entries: SrtEntry[] = [];
  const normalized = content.replace(/\r/g, "").trim();
  const blocks = normalized.split(/\n{2,}/);

  for (const block of blocks) {
    const lines = block.trim().split("\n");
    if (lines.length < 3) continue;

    const index = parseInt(lines[0], 10);
    const timeParts = lines[1].split(" --> ");
    if (timeParts.length !== 2) continue;

    const startMs = timeToMs(timeParts[0].trim());
    const endMs = timeToMs(timeParts[1].trim());
    const text = lines.slice(2).join("\n");

    entries.push({ index, startMs, endMs, text });
  }

  return entries;
}

function timeToMs(time: string): number {
  const normalized = time.replace(",", ".");
  const parts = normalized.split(":");
  const hours = parseInt(parts[0], 10);
  const minutes = parseInt(parts[1], 10);
  const [secs, ms] = parts[2].split(".");
  return (
    hours * 3600000 +
    minutes * 60000 +
    parseInt(secs, 10) * 1000 +
    parseInt(ms || "0", 10)
  );
}

interface SubtitleProps {
  srtFile: string;
}

export const Subtitle: React.FC<SubtitleProps> = ({ srtFile }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const [entries, setEntries] = useState<SrtEntry[]>([]);

  useEffect(() => {
    fetch(staticFile(srtFile))
      .then((res) => res.text())
      .then((text) => {
        setEntries(parseSrt(text));
      })
      .catch((err) => {
        console.warn("Cannot load subtitle file:", err);
      });
  }, [srtFile]);

  const currentTimeMs = (frame / fps) * 1000;

  const currentEntry = entries.find(
    (e) => currentTimeMs >= e.startMs && currentTimeMs <= e.endMs
  );

  if (!currentEntry) return null;

  const entryDurationMs = currentEntry.endMs - currentEntry.startMs;
  const progressMs = currentTimeMs - currentEntry.startMs;
  const progress = progressMs / entryDurationMs;

  const fadeIn = interpolate(progress, [0, 0.1], [0, 1], {
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(progress, [0.9, 1], [1, 0], {
    extrapolateLeft: "clamp",
  });
  const opacity = fadeIn * fadeOut;
  const translateY = interpolate(progress, [0, 0.1], [8, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: 100,
      }}
    >
      <div
        style={{
          opacity,
          transform: `translateY(${translateY}px)`,
          padding: "12px 40px",
          borderRadius: 8,
          background: "rgba(0, 0, 0, 0.55)",
          backdropFilter: "blur(8px)",
          maxWidth: "80%",
        }}
      >
        <div
          style={{
            fontSize: 36,
            color: "#ffffff",
            fontFamily:
              '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
            fontWeight: 500,
            textAlign: "center",
            lineHeight: 1.5,
            textShadow: "0 2px 8px rgba(0,0,0,0.5)",
            letterSpacing: "0.02em",
          }}
        >
          {currentEntry.text}
        </div>
      </div>
    </AbsoluteFill>
  );
};
