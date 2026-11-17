/** The real attachment preview over a page of its own: a picture, its thumbnail kept with a sent message, and a video. */
import React from 'react';
import { createRoot } from 'react-dom/client';
import { AttachmentPreview, type AttachmentPreviewItem } from '../chat/src/components/AttachmentPreview';
import '../shell/shell.css';
import '../chat/src/chat.css';

/* a 600 × 400 picture, drawn here so the fixture needs no file */
const canvas = document.createElement('canvas');
canvas.width = 600;
canvas.height = 400;
const g = canvas.getContext('2d')!;
g.fillStyle = '#2b6cb0';
g.fillRect(0, 0, 600, 400);
g.fillStyle = '#fff';
g.fillRect(40, 40, 200, 120);
const picture = canvas.toDataURL('image/png');

const items: Record<string, AttachmentPreviewItem> = {
  picture: { name: 'screenshot.png', kind: 'image', url: picture, mediaType: 'image/png' },
  thumb: { name: 'screenshot.png', kind: 'image', url: picture, mediaType: 'image/png', thumbOnly: true },
};

function Fixture() {
  const [open, setOpen] = React.useState<string | null>(null);
  (window as any).attachmentPreviewFixture = { open: setOpen, opened: () => open };
  return (
    <>
      <div className="of-chat" style={{ padding: 16 }}>
        <button type="button" id="behind">Behind</button>
      </div>
      {open ? <AttachmentPreview item={items[open]!} onClose={() => setOpen(null)} /> : null}
      <div id="of-chat-layer" className="of-chat" />
    </>
  );
}

createRoot(document.getElementById('root')!).render(<Fixture />);
