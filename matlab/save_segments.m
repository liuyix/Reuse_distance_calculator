function save_segments(fname)

[X, Y] = ginput;
fid = fopen(fname, 'w');
fprintf(fid, '%.0f\n', X);

end

