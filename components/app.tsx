'use client';

import * as React from 'react';
import { Room, RoomEvent } from 'livekit-client';
import { motion } from 'motion/react';
import { RoomAudioRenderer, RoomContext, StartAudio } from '@livekit/components-react';
import { toastAlert } from '@/components/alert-toast';
import { SessionView } from '@/components/session-view';
import { Toaster } from '@/components/ui/sonner';
import { Welcome } from '@/components/welcome';
import useConnectionDetails from '@/hooks/useConnectionDetails';
import type { AppConfig } from '@/lib/types';

const MotionSessionView = motion.create(SessionView);
const MotionWelcome = motion.create(Welcome);

interface AppProps {
  appConfig: AppConfig;
}

export function App({ appConfig }: AppProps) {
  const [sessionStarted, setSessionStarted] = React.useState(false);
  const [ragEnabled, setRagEnabled] = React.useState(true); // RAG toggle state
  const { suportsChatInput, suportsVideoInput, suportsScreenShare, startButtonText } = appConfig;

  const capabilities = {
    suportsChatInput,
    suportsVideoInput,
    suportsScreenShare,
  };

  const connectionDetails = useConnectionDetails();

  const room = React.useMemo(() => new Room(), []);

  // useEffect to handle RAG toggling
  React.useEffect(() => {
    if (ragEnabled) {
      console.log('RAG enabled - loading documentation tools');
      // You could load embeddings, set up tools, etc.
    } else {
      console.log('RAG disabled - removing documentation tools');
      // You could clear context, remove tools, etc.
    }
  }, [ragEnabled]);

  React.useEffect(() => {
    const onDisconnected = () => {
      setSessionStarted(false);
    };
    const onMediaDevicesError = (error: Error) => {
      toastAlert({
        title: 'Encountered an error with your media devices',
        description: `${error.name}: ${error.message}`,
      });
    };
    room.on(RoomEvent.MediaDevicesError, onMediaDevicesError);
    room.on(RoomEvent.Disconnected, onDisconnected);
    return () => {
      room.off(RoomEvent.Disconnected, onDisconnected);
      room.off(RoomEvent.MediaDevicesError, onMediaDevicesError);
    };
  }, [room]);

  React.useEffect(() => {
    if (sessionStarted && room.state === 'disconnected' && connectionDetails) {
      Promise.all([
        room.connect(connectionDetails.serverUrl, connectionDetails.participantToken),
      ]).then(() => {
        // Set participant metadata with RAG state
        room.localParticipant.setMetadata(JSON.stringify({ ragEnabled }));
        // Enable microphone after connection is established
        return room.localParticipant.setMicrophoneEnabled(true);
      }).catch((error) => {
        toastAlert({
          title: 'There was an error connecting to the agent',
          description: `${error.name}: ${error.message}`,
        });
      });
    }
    return () => {
      room.disconnect();
    };
  }, [room, sessionStarted, connectionDetails, ragEnabled]);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between border-b px-4 py-2">
        <h1 className="text-lg font-semibold">Voice Assistant</h1>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={ragEnabled}
              onChange={(e) => setRagEnabled(e.target.checked)}
              className="rounded"
            />
            RAG Enabled
          </label>
        </div>
      </header>
      <MotionWelcome
        key="welcome"
        startButtonText={startButtonText}
        onStartCall={() => setSessionStarted(true)}
        onFastDemo={() => {
          setRagEnabled(false);
          setSessionStarted(true);
        }}
        onSmartDemo={() => {
          setRagEnabled(true);
          setSessionStarted(true);
        }}
        disabled={sessionStarted}
        initial={{ opacity: 0 }}
        animate={{ opacity: sessionStarted ? 0 : 1 }}
        transition={{ duration: 0.5, ease: 'linear', delay: sessionStarted ? 0 : 0.5 }}
      />

      <RoomContext.Provider value={room}>
        <RoomAudioRenderer />
        <StartAudio label="Start Audio" />
        {/* --- */}
        <MotionSessionView
          key="session-view"
          capabilities={capabilities}
          sessionStarted={sessionStarted}
          disabled={!sessionStarted}
          initial={{ opacity: 0 }}
          animate={{ opacity: sessionStarted ? 1 : 0 }}
          transition={{
            duration: 0.5,
            ease: 'linear',
            delay: sessionStarted ? 0.5 : 0,
          }}
        />
      </RoomContext.Provider>

      <Toaster />
    </div>
  );
}
