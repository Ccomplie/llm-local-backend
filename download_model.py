# # 模型下载
from modelscope import snapshot_download
# model_dir = snapshot_download('deepseek-ai/DeepSeek-R1-Distill-Qwen-7B', cache_dir='./models')

# #模型下载
# # #模型下载
# from modelscope import snapshot_download
# model_dir = snapshot_download('deepseek-ai/DeepSeek-R1-0528-Qwen3-8B', cache_dir='./models', max_workers=4)

#模型下载
# from modelscope import snapshot_download
# model_dir = snapshot_download('deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B', cache_dir='./models', max_workers=4)


#或者在命令行中：
# modelscope download --model deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B --cache-dir ./models



model_dir = snapshot_download('Qwen/Qwen3-32B-fp8', cache_dir='./models')
model_dir = snapshot_download('Qwen/Qwen3-32B-AWQ', cache_dir='./models')
model_dir = snapshot_download('Qwen/Qwen3-8B', cache_dir='./models')
# model_dir = snapshot_download('Qwen/Qwen3-30B-A3B-Instruct-2507', cache_dir='./models')
# model_dir = snapshot_download('deepseek-ai/DeepSeek-R1-Distill-Qwen-14B', cache_dir='./models')

model_dir = snapshot_download('deepseek-ai/DeepSeek-R1-Distill-Qwen-7B', cache_dir='./models')


