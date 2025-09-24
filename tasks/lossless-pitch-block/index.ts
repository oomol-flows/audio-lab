import type { Context } from "@oomol/types/oocana";
import fs from "fs";
import FormData from "form-data";
import fetch from "node-fetch";

//#region generated meta
type Inputs = {
  file: string;
  pitch: number;
  fp: boolean;
  tp: boolean;
};
type Outputs = {
  download_url: string;
};
//#endregion

interface StartTaskResponse {
  success?: boolean;
  music_id?: string;
  message?: string;
}

interface StatusResponse {
  success?: boolean;
  status?: string;
  message?: string;
}

interface DownloadResponse {
  success?: boolean;
  data?: {
    url?: string;
  };
  message?: string;
}

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export default async function(
  params: Inputs,
  context: Context<Inputs, Outputs>
): Promise<Outputs> {
  const { file, pitch, fp, tp } = params;
  
  console.log(`Starting lossless pitch shift...\nfile: ${file}\npitch: ${pitch}\nfp: ${fp}\ntp: ${tp}`);

  try {
    // Step 1: 开始任务
    console.log("start task...")

    const formData = new FormData();
    
    // 读取文件并添加到formData
    const fileBuffer = fs.readFileSync(file);
    const fileName = file.split('/').pop() || 'audio.mp3';
    
    formData.append('file', fileBuffer, {filename: fileName});
    formData.append('pitch', pitch.toString());
    formData.append('fp', fp.toString());
    formData.append('tp', tp.toString());

    const startResponse = await fetch(
      'https://console.oomol.com/api/tasks/tuanzi/lossless-pitch/start',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${context.OOMOL_LLM_ENV.apiKey}`,
        },
        body: formData as any,
        signal: AbortSignal.timeout(30000)
      }
    );

    if (!startResponse.ok) {
        const r = await startResponse.json()
        throw new Error(`开始任务失败: HTTP ${JSON.stringify(r)}`);
    }

    const startData = await startResponse.json() as StartTaskResponse;
    
    if (startData.success !== true) {
      throw new Error(`开始任务失败: ${startData.message || '未知错误'}`);
    }

    const musicId = startData.music_id;
    if (!musicId) {
      throw new Error('未获取到music_id');
    }

    console.log("task started")

    // Step 2: 查询任务状态
    console.log("check task status...")

    // 首次调用前延迟5秒
    await sleep(5000);

    let statusResponse: StatusResponse;
    let attempts = 0;
    const maxAttempts = 60; // 最多尝试60次，5分钟

    while (attempts < maxAttempts) {
      try {
        const statusRes = await fetch(
          `https://console.oomol.com/api/tasks/tuanzi/lossless-pitch/status/${musicId}`,
          {
            headers: {
              'Authorization': `Bearer ${context.OOMOL_LLM_ENV.apiKey}`,
            },
            signal: AbortSignal.timeout(10000)
          }
        );

        if (!statusRes.ok) {
          throw new Error(`状态查询失败: HTTP ${statusRes.status}`);
        }

        statusResponse = await statusRes.json() as StatusResponse;

        if (statusResponse.success === true) {
          console.log("task is success")
          break;
        }

        console.log(`task is running, check: (${attempts + 1}/${maxAttempts})`)

        attempts++;
        await sleep(5000); // 5秒后重试

      } catch (error) {
        const fetchError = error as Error;
        context.preview({
          type: "text",
          data: `状态查询失败: ${fetchError.message}`
        });
        attempts++;
        await sleep(5000);
      }
    }

    if (attempts >= maxAttempts) {
      throw new Error('任务处理超时，请稍后重试');
    }

    // Step 3: 获取下载地址
    console.log("get download url...")

    const downloadResponse = await fetch(
      `https://console.oomol.com/api/tasks/tuanzi/lossless-pitch/download/${musicId}`,
      {
        signal: AbortSignal.timeout(10000),
        headers: {
            'Authorization': `Bearer ${context.OOMOL_LLM_ENV.apiKey}`,
        }
      }
    );

    if (!downloadResponse.ok) {
      throw new Error(`获取下载地址失败: HTTP ${downloadResponse.status}`);
    }

    const downloadData = await downloadResponse.json() as DownloadResponse;
    
    if (downloadData.success !== true) {
      throw new Error(`获取下载地址失败: ${downloadData.message || '未知错误'}`);
    }

    const downloadUrl = downloadData.data?.url;
    if (!downloadUrl) {
      throw new Error('未获取到下载地址');
    }

    console.log(`task is done, download file url: ${downloadUrl}`)

    return {
      download_url: encodeURI(downloadUrl)
    };

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '未知错误';
    throw new Error(`无损变调处理失败: ${errorMessage}`);
  }
}