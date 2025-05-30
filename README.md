# 功能说明
调用大模型API翻译已识别为md文件的学术论文（暂定）

# 更新日志
2025.4.2 v1.0 实现基本功能（导入md、过滤无效信息、自动翻译、输出md）

2025.4.2 v1.1 适配UI界面

2025.4.3 v1.2 增加并行处理功能（按章节拆分，各自创建对话进程），增加并行处理进度条

2025.4.3 v1.2.1 修改执行逻辑，现在导入md文件后将立刻执行过滤操作

2025.4.3 v1.2.2 修改读取操作逻辑，现在第二个拖放进去的md文件将覆盖第一个；增添了翻译进程保护，若翻译正在进行中，则不读取拖放上来的文件。修改过滤逻辑，增添识别“# References”大小写支持，增添对“# Acknowledgements”、“# acknowledgment”、“# bibliography”的识别。

2025.4.4 v1.2.3 （1）修复了翻译章节数过多时翻译输出空文件的问题，增加了翻译成功确认步骤，若未接收到模型返回的翻译结果，则再次请求，默认最大请求数为3；（2）增加了Deepseek API支持

2025.4.4 v1.3 支持多文件翻译，重新设计多文件翻译的UI界面

2025.4.5 修复了在UI界面填写API-key后不会将其同步到后端的BUG

2025.4.5 v1.3.1 增加指定缓存文件及结果输出文件位置功能，缓存文件为各章节翻译结果，在最终翻译结束时会弹出提示框询问是否删除缓存文件，若选择是则会删除缓存文件夹，若选择否则保留缓存文件夹

2025.4.13 修复了使用Deepseek-V3翻译时由于请求速度过快导致程序卡死的问题，为每次请求增添延迟，同时在API请求失败后自动重连的机制中增添对Rate Limit

2025.5.8 修复了上一次更新中出现的导致程序无法运行的严重BUG

2025.5.24 修复了最终不输出合并后的翻译结果文件的问题；修复了翻译中点击日志区导致卡死的问题；优化了对超长章节的支持，现在可以对过长的章节进一步分块，依次翻译每一个块，并且上一个块的最后五段将作为下一块的输入，以此保持一定程度上的连贯性；优化了缓存文件和最终结果文件的逻辑，降低内存占用
