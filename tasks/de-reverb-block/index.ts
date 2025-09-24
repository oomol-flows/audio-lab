import type { Context } from "@oomol/types/oocana";
import fs from "fs";
import FormData from "form-data";
import fetch from "node-fetch";

//#region generated meta
type Inputs = {
  file: string;
};
type Outputs = {
  download_url: string;
};
//#endregion

interface ApiResponse {
  success?: boolean;
  music_id?: string;
  data?: {
    url?: string;
  };
}

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function startDeReverb(filePath: string, apiKey: string): Promise<string> {
  const formData = new FormData();
  
  // 读取文件并添加到formData
  const fileBuffer = fs.readFileSync(filePath);
  const fileName = filePath.split('/').pop() || 'audio.mp3';
  
  formData.append('file', fileBuffer, {
    filename: fileName,
    contentType: 'audio/mpeg'
  });
  formData.append('style', '1');

  const response = await fetch('https://console.oomol.com/api/tasks/tuanzi/de-reverb/start', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
    },
    body: formData as any,
    signal: AbortSignal.timeout(30000)
  });

  if (!response.ok) {
    const r = await response.json();
    throw new Error(`开始任务失败: HTTP ${JSON.stringify(r)}`);
  }

  const result = await response.json() as ApiResponse;
  
  if (result.success !== true) {
    throw new Error(`开始去混响任务失败: ${JSON.stringify(result)}`);
  }
  
  if (!result.music_id) {
    throw new Error('未获取到music_id');
  }

  return result.music_id;
}

async function checkTaskStatus(musicId: string, apiKey: string): Promise<boolean> {
  const response = await fetch(`https://console.oomol.com/api/tasks/tuanzi/de-reverb/status/${musicId}`, {
    headers: {
      'Authorization': `Bearer ${apiKey}`,
    },
    signal: AbortSignal.timeout(10000)
  });
  
  if (!response.ok) {
    throw new Error(`查询任务状态失败: HTTP ${response.status}`);
  }

  const result = await response.json() as ApiResponse;
  return result.success === true;
}

async function getDownloadUrl(musicId: string, apiKey: string): Promise<string> {
  const response = await fetch(`https://console.oomol.com/api/tasks/tuanzi/de-reverb/download/${musicId}`, {
    headers: {
      'Authorization': `Bearer ${apiKey}`,
    },
    signal: AbortSignal.timeout(10000)
  });
  
  if (!response.ok) {
    throw new Error(`获取下载地址失败: HTTP ${response.status}`);
  }

  const result = await response.json() as ApiResponse;
  
  if (!result.data?.url) {
    throw new Error('未获取到下载地址');
  }

  return result.data.url;
}

export default async function(params: Inputs, context: Context<Inputs, Outputs>): Promise<Outputs> {
  try {
    console.log("starting de-reverb task");

    // 步骤1: 开始去混响任务
    const musicId = await startDeReverb(params.file, context.OOMOL_LLM_ENV.apiKey);

    console.log(`task started, id: ${musicId}`);

    // 步骤2: 查询任务状态，首次调用延迟5秒
    await sleep(5000);
    
    let isCompleted = false;
    let retryCount = 0;
    const maxRetries = 60; // 最多等待5分钟
    
    while (!isCompleted && retryCount < maxRetries) {
      isCompleted = await checkTaskStatus(musicId, context.OOMOL_LLM_ENV.apiKey);
      
      if (!isCompleted) {
        console.log(`task is running, check: (${retryCount + 1}/${maxRetries})`);
        await sleep(5000);
        retryCount++;
      }
    }

    if (!isCompleted) {
      throw new Error('任务超时未完成');
    }

    console.log("task is done")

    // 步骤3: 获取下载地址
    const downloadUrl = await getDownloadUrl(musicId, context.OOMOL_LLM_ENV.apiKey);
    
    console.log(`donwload file url: ${downloadUrl}`)

    return { download_url: encodeURI(downloadUrl) };
    
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '未知错误';
    throw new Error(`去混响任务失败: ${errorMessage}`);
  }
}