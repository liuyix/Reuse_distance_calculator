function mark_segments(trace_filename)

% 读取reuse distance，人工标注phase分割点，将结果保存到out_filename中
% input: reuse distance trace file name, segments output file name

data = load(trace_filename);
plot(data);

[X, Y] = ginput;
fid = fopen([trace_filename,'.seg'], 'w');
fprintf(fid, '%.0f\n', X);
fclose(fid)
end

