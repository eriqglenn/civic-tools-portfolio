using System;
using System.IO;
using System.Threading;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;

// Convert an explicitly selected Windows speech input into a PCM Stream for System.Speech.
namespace Ledger.Audio {
    [ComImport,Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class DeviceEnumerator {}
    [ComImport,Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"),InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IDeviceEnumerator {
        void EnumAudioEndpoints(int flow,uint states,out IntPtr devices);
        void GetDefaultAudioEndpoint(int flow,int role,out IDevice device);
    }
    [ComImport,Guid("D666063F-1587-4E43-81F1-B948E807363F"),InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IDevice {
        void Activate(ref Guid id,uint context,IntPtr paramsPtr,out IntPtr result);
        void OpenPropertyStore(int mode,out IntPtr store);
        void GetId([MarshalAs(UnmanagedType.LPWStr)]out string id);
    }

    public sealed class MicrophoneStream : Stream {
        private readonly dynamic device;
        private readonly IStream input;
        private volatile bool closed;
        private long position;
        private int peak;

        // Measure PCM before recognition: SAPI does not emit level events for custom streams.
        public static int SignalLevel(byte[] buffer, int size) {
            int maximum = 0;
            for (int i = 0; i + 1 < size; i += 2) {
                int sample = (short)(buffer[i] | (buffer[i + 1] << 8));
                maximum = Math.Max(maximum, Math.Abs(sample));
            }
            return (int)Math.Round(100 * Math.Sqrt(maximum / 32768.0));
        }
        public int TakeLevel() { return Interlocked.Exchange(ref peak, 0); }
        public static string DefaultEndpoint() {
            var devices = (IDeviceEnumerator)new DeviceEnumerator();
            IDevice endpoint; devices.GetDefaultAudioEndpoint(1, 0, out endpoint);
            string id; endpoint.GetId(out id); return id;
        }
        public string DeviceName { get; private set; }

        private static dynamic Create(string progId) {
            return Activator.CreateInstance(Type.GetTypeFromProgID(progId, true));
        }

        public static Dictionary<string,string> Devices() {
            dynamic recognizer = Create("SAPI.SpInprocRecognizer");
            var result = new Dictionary<string,string>();
            foreach (dynamic token in recognizer.GetAudioInputs()) {
                result.Add((string)token.Id,(string)token.GetDescription());
            }
            return result;
        }

        public MicrophoneStream(string id) {
            dynamic recognizer = Create("SAPI.SpInprocRecognizer");
            foreach (dynamic token in recognizer.GetAudioInputs()) {
                if (!String.Equals(id,(string)token.Id,StringComparison.OrdinalIgnoreCase)) continue;
                DeviceName = token.GetDescription();
                device = token.CreateInstance();
                input = (IStream)(object)device;
                dynamic format = Create("SAPI.SpAudioFormat");
                format.Type = 18; // SAFT16kHz16BitMono
                device.Format = format;
                device.SetState(3); // SASRun
                return;
            }
            throw new IOException("The selected microphone is disconnected.");
        }

        public override int Read(byte[] buffer, int offset, int count) {
            if (closed || count == 0) return 0;
            int requested = Math.Min(4096,count);
            byte[] chunk = offset == 0 ? buffer : new byte[requested];
            IntPtr actual = Marshal.AllocCoTaskMem(sizeof(int));
            try {
                input.Read(chunk,requested,actual);
                int size = Marshal.ReadInt32(actual);
                if (offset != 0) Buffer.BlockCopy(chunk,0,buffer,offset,size);
                int level = SignalLevel(chunk, size);
                int previous;
                do { previous = peak; if (level <= previous) break; }
                while (Interlocked.CompareExchange(ref peak,level,previous) != previous);
                position += size;
                return size;
            } catch (COMException) {
                if (closed) return 0;
                throw;
            } finally { Marshal.FreeCoTaskMem(actual); }
        }
        protected override void Dispose(bool disposing) {
            if (!closed) {
                closed = true;
                try { device.SetState(0); } catch (COMException) { }
            }
            base.Dispose(disposing);
        }
        public override bool CanSeek { get { return false; } }
        public override bool CanWrite { get { return false; } }
        public override bool CanRead { get { return !closed; } }
        public override long Position { get { return position; } set { throw new NotSupportedException(); } }
        public override long Length { get { return Int64.MaxValue; } }
        public override void Flush() {}
        public override void SetLength(long value) { throw new NotSupportedException(); }
        public override long Seek(long offset, SeekOrigin origin) {
            // SAPI queries the cursor before starting a forward-only capture.
            if ((origin == SeekOrigin.Current && offset == 0) || (origin == SeekOrigin.Begin && offset == position)) return position;
            throw new NotSupportedException();
        }
        public override void Write(byte[] b, int o, int c) { throw new NotSupportedException(); }
    }
}

